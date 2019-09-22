"""
Morphology module
=================
:synopsis: Create foam morphology in CAD format.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from __future__ import print_function
import os
import numpy as np
from blessings import Terminal
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepTools import breptools_Read, breptools_Write
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Compound
from OCC.Display.SimpleGui import init_display
from OCC.Extend.TopologyUtils import TopologyExplorer
from . import geo_tools as gt


def make_walls(fname, wall_thickness, clean):
    """Add walls to a tessellated foam.

    Walls are created in gmsh CAD format. Geometry is then converted to BREP
    format, in which it is moved to periodic box using pythonOCC (separately
    for cells and walls). Final file merges generated file in gmsh-readable
    format.

    FileTessellation.geo -> FileCells.geo + FileWalls.geo ->
    FileCellsBox.brep + FileWallsBox.brep -> FileMorphology.geo

    Args:
        fname (str): base filename
        wall_thickness (float): wall thickness parameter
        clean (bool): delete redundant files if True
    """
    term = Terminal()
    # create walls
    iname = fname + "Tessellation.geo"
    cname = fname + "Cells.geo"
    wname = fname + "Walls.geo"
    print(
        term.yellow
        + "Starting from file {}.".format(iname)
        + term.normal
    )
    ncells = add_walls(iname, cname, wname, wall_thickness)
    # move foam to a periodic box and save it to a file
    iname = cname
    cname = fname + "CellsBox.brep"
    wname = fname + "WallsBox.brep"
    to_box(iname, cname, wname, ncells)
    # create morphology file
    oname = fname + "Morphology.geo"
    gt.merge_and_label_geo([cname, wname], oname)
    # delete redundant files
    if clean:
        clean_files()
    print(
        term.yellow
        + "Prepared file {}.".format(oname)
        + term.normal
    )


def add_walls(iname, cname, wname, wall_thickness):
    """Create walls by shrinking each cell.

    Uses files in gmsh CAD format.

    Args:
        iname (str): input filename
        cname (str): output filename with cells
        wname (str): output filename with walls
        wall_thickness (float): wall thickness parameter

    Returns:
        int: number of cells
    """
    # read Neper foam
    sdat = gt.read_geo(iname)  # string data
    # Neper creates physical surfaces, which we don't want
    sdat.pop('physical_surface')
    # remove orientation, OpenCASCADE compatibility
    gt.fix_strings(sdat['line_loop'])
    gt.fix_strings(sdat['surface_loop'])
    # create walls
    edat = gt.extract_data(sdat)
    cedat, wedat = gt.create_walls(edat, wall_thickness)
    sdat = gt.collect_strings(cedat)
    gt.save_geo(cname, sdat)
    sdat = gt.collect_strings(wedat)
    gt.save_geo(wname, sdat)
    ncells = len(sdat['volume'])
    return ncells


def to_box(iname, cname, wname, ncells, method='pythonocc'):
    """Move foam to periodic box.

    Remove point duplicity, restore OpenCASCADE compatibility, define periodic
    and physical surfaces.

    Only pythonocc method is currently functional.

    Args:
        iname (str): input filename
        cname (str): output filename with cells
        wname (str): output filename with walls
        ncells (int): number of cells
        method (str): gmsh or pythonocc (default)
    """
    if method == 'gmsh':
        # oname = 'temp.geo'
        # move foam to a periodic box and save it to a file
        gt.move_to_box(iname, "move_to_box.geo", cname, ncells)
    elif method == 'pythonocc':
        # convert to BREP
        tname1 = "temp.brep"
        gt.geo2brep(iname, tname1)
        # move foam to a periodic box and save it to files
        move_to_box(tname1, cname, wname, False)
    else:
        raise Exception('Only gmsh and pythonocc methods implemented.')


def finalize_geo(iname, oname, verbose, method='pythonocc'):
    """Define periodic surfaces and physical volumes.

    Also remove point duplicity and restore OpenCASCADE compatibility.
    """
    # read boxed foam
    sdat = gt.read_geo(iname)  # string data
    edat = gt.extract_data(sdat)  # extracted data
    # duplicity of points, lines, etc. was created during moving to a box
    gt.remove_duplicity(edat)
    # restore OpenCASCADE compatibility
    gt.split_loops(edat, 'line_loop')
    gt.split_loops(edat, 'surface_loop')
    # identification of physical surfaces for boundary conditions
    surf0 = gt.surfaces_in_plane(edat, 0.0, 2)
    if verbose:
        print('Z=0 surface IDs: {}'.format(surf0))
    surf1 = gt.surfaces_in_plane(edat, 1.0, 2)
    if verbose:
        print('Z=1 surface IDs: {}'.format(surf1))
    surf = gt.other_surfaces(edat, surf0 + surf1)
    if verbose:
        print('other boundary surface IDs: {}'.format(surf))
    # Physical surfaces create problems in mesh conversion step. Bug in gmsh?
    # Boundaries will be defined in fenics/dolfin directly.
    # edat['physical_surface'] = {1:surf0, 2:surf1, 3:surf}
    # identification of periodic surfaces for periodic mesh creation
    edat['periodic_surface_X'] = gt.periodic_surfaces(
        edat, surf, np.array([1, 0, 0])
    )
    edat['periodic_surface_Y'] = gt.periodic_surfaces(
        edat, surf, np.array([0, 1, 0])
    )
    if verbose:
        print(
            'surface IDs periodic in X: {}'.format(edat['periodic_surface_X'])
        )
        print(
            'surface IDs periodic in Y: {}'.format(edat['periodic_surface_Y'])
        )
    if method == 'pythonocc':
        edat['physical_volume'] = {'1': edat['volume'].keys()}
    # restore_sizing(edat)
    # save the final foam
    sdat = gt.collect_strings(edat)
    gt.save_geo(oname, sdat)


def translate_topods_from_vector(brep, vec, copy=False):
    """Translate a brep over a vector.

    Args:
        brep (BRep): the Topo_DS to translate
        vec (gp_Vec): the vector defining the translation
        copy (bool): copies to brep if True
    """
    trns = gp_Trsf()
    trns.SetTranslation(vec)
    brep_trns = BRepBuilderAPI_Transform(brep, trns, copy)
    brep_trns.Build()
    return brep_trns.Shape()


def slice_and_move(obj, box, vec):
    """Cut, move, and join and object

    One object is cut by another object. Sliced part is moved by a vector.
    Moved part is joined with non-moved part.

    Args:
        obj (Solid): object to be cut
        box (Solid): object used for cutting
        vec (gp_Vec): vector defining the offset
    """
    print('Solids before slicing: {}'.format(len(obj)))
    newsol = []
    for solid in obj:
        cut = BRepAlgoAPI_Cut(solid, box).Shape()
        comm = BRepAlgoAPI_Common(solid, box).Shape()
        comm = translate_topods_from_vector(comm, vec)
        newsol.append(cut)
        texp = TopologyExplorer(comm)
        if list(texp.solids()):
            newsol.append(comm)
    print('Solids after slicing: {}'.format(len(newsol)))
    return newsol


def create_compound(obj, compound, builder):
    """Add objects to compound using builder.

    Args:
        obj (list): list of objects to be added to compound
        compound (obj): the compound
        builder (obj): BREP builder
    """
    for solid in obj:
        builder.Add(compound, solid)


def move_to_box(iname, cname, wname, visualize=False):
    """Move foam to periodic box.

    Works on BREP files. Information about physical volumes is lost.

    Args:
        iname (str): input filename
        cname (str): output filename with cells
        wname (str): output filename with walls
        visualize (bool): show picture of foam morphology in box if True
    """
    cells = TopoDS_Shape()
    builder = BRep_Builder()
    breptools_Read(cells, iname, builder)
    texp = TopologyExplorer(cells)
    solids = list(texp.solids())

    cells = TopoDS_Compound()
    builder.MakeCompound(cells)

    box = BRepPrimAPI_MakeBox(gp_Pnt(1, -1, -1), 3, 3, 3).Shape()
    vec = gp_Vec(-1, 0, 0)
    solids = slice_and_move(solids, box, vec)
    box = BRepPrimAPI_MakeBox(gp_Pnt(-3, -1, -1), 3, 3, 3).Shape()
    vec = gp_Vec(1, 0, 0)
    solids = slice_and_move(solids, box, vec)
    box = BRepPrimAPI_MakeBox(gp_Pnt(-1, 1, -1), 3, 3, 3).Shape()
    vec = gp_Vec(0, -1, 0)
    solids = slice_and_move(solids, box, vec)
    box = BRepPrimAPI_MakeBox(gp_Pnt(-1, -3, -1), 3, 3, 3).Shape()
    vec = gp_Vec(0, 1, 0)
    solids = slice_and_move(solids, box, vec)
    box = BRepPrimAPI_MakeBox(gp_Pnt(-1, -1, 1), 3, 3, 3).Shape()
    vec = gp_Vec(0, 0, -1)
    solids = slice_and_move(solids, box, vec)
    box = BRepPrimAPI_MakeBox(gp_Pnt(-1, -1, -3), 3, 3, 3).Shape()
    vec = gp_Vec(0, 0, 1)
    solids = slice_and_move(solids, box, vec)
    create_compound(solids, cells, builder)
    breptools_Write(cells, cname)
    if visualize:
        display, start_display, _, _ = init_display()
        display.DisplayShape(cells, update=True)
        start_display()
    box = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 1, 1, 1).Shape()
    walls = BRepAlgoAPI_Cut(box, cells).Shape()
    breptools_Write(walls, wname)
    if visualize:
        display, start_display, _, _ = init_display()
        display.DisplayShape(walls, update=True)
        start_display()


def clean_files():
    """Delete unnecessary files."""
    flist = [
        'move_to_box.geo',
        'temp.geo',
        'temp.brep',
    ]
    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)
