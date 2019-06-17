"""
Morphology module
=================
:synopsis: Create foam morphology in CAD format.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
.. moduleauthor:: Mohammad Marvi-Mashhadi <mohammad.marvi@imdea.org>
"""
from __future__ import print_function
import os
import shutil
import numpy as np
from blessings import Terminal
from . import geo_tools as gt


def make_walls(fname, wall_thickness, clean, verbose):
    """Add walls to a tessellated foam.

    It is assumed that input file uses gmsh built-in kernel. Final geometry is
    created in the OpenCASCADE kernel.

    FileTessellation.geo -> FileWalls.geo -> FileWallsBox.geo ->
    FileMorphology.geo

    Args:
        fname (str): base filename
        wall_thickness (float): wall thickness parameter
        clean (bool): delete redundant files if True
        verbose (bool): print additional info to stdout if True
    """
    term = Terminal()
    # create walls
    iname = fname + "Tessellation.geo"
    oname = fname + "Walls.geo"
    print(
        term.yellow
        + "Starting from file {}.".format(iname)
        + term.normal
    )
    ncells = add_walls(iname, oname, wall_thickness)
    # move foam to a periodic box and save it to a file
    iname = oname
    oname = fname + "WallsBox.geo"
    to_box(iname, oname, ncells, verbose)
    # overwrite morphology file
    iname = oname
    oname = fname + "Morphology.geo"
    shutil.copy2(iname, oname)
    # delete redundant files
    if clean:
        clean_files()
    print(
        term.yellow
        + "Prepared file {}.".format(oname)
        + term.normal
    )


def add_walls(iname, oname, wall_thickness):
    """Create walls by shrinking each cell.

    Uses files in gmsh CAD format.

    Args:
        iname (str): input filename
        oname (str): output filename
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
    gt.create_walls(edat, wall_thickness)
    sdat = gt.collect_strings(edat)
    gt.save_geo(oname, sdat)
    ncells = len(sdat['volume'])
    return ncells


def to_box(iname, oname, ncells, verbose):
    """Move foam to periodic box.

    Remove point duplicity, restore OpenCASCADE compatibility, define periodic
    and physical surfaces.

    Args:
        iname (str): input filename
        oname (str): output filename
        wall_thickness (float): wall thickness parameter
        ncells (int): number of cells
        verbose (bool): print additional info to stdout if True
    """
    tname = 'temp.geo'
    # move foam to a periodic box and save it to a file
    gt.move_to_box(iname, "move_to_box.geo", tname, range(1, ncells + 1))
    # read boxed foam
    sdat = gt.read_geo(tname)  # string data
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
    surf = gt.other_surfaces(edat, surf0, surf1)
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
    # restore_sizing(edat)
    # save the final foam
    sdat = gt.collect_strings(edat)
    gt.save_geo(oname, sdat)


def clean_files():
    """Delete unnecessary files."""
    flist = [
        'move_to_box.geo',
        'temp.geo',
    ]
    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)
