#!/usr/bin/env python
"""Python script, which organizes creation of the foam.

First, the geometric tessellation is performed so that the resulting foam has
the correct bubble size distribution. Then several mesh conversions are made to
obtain the foam image in desired format. Finally, foam is voxelized to desired
foam density and struts are optionally added.

"""
from __future__ import division, print_function
import os
import sys
import datetime
import shutil
import subprocess as sp
from blessings import Terminal
import yamlargparse as yp
from scipy.optimize import minimize_scalar
from . import packing
from . import tessellation
from . import periodicBox
from . import vtkconv
from . import geo_tools
# Creates terminal for colour output
TERM = Terminal()


def parse():
    """Parse arguments using yamlargparse and call generate function."""
    prs = yp.ArgumentParser(
        prog='foamgen',
        error_handler=yp.usage_and_exit_error_handler,
        description='Generate foam morphology.')
    prs.add_argument('-c', '--config', action=yp.ActionConfigFile,
                     help='name of config file')
    prs.add_argument('-f', '--filename', default='Foam',
                     help='base filename')
    prs.add_argument('-p', '--pack.active', default=False,
                     action='store_true', help='create sphere packing')
    prs.add_argument('--pack.dsize', default=1,
                     help='domain size')
    prs.add_argument('--pack.ncells', default=27,
                     help='number of cells')
    prs.add_argument('--pack.shape', default=0.2,
                     help='sphere size distribution shape factor')
    prs.add_argument('--pack.scale', default=0.2,
                     help='sphere size distribution scale factor')
    prs.add_argument('--pack.alg', default='fba',
                     help='packing algorithm')
    prs.add_argument('-t', '--tess.active', default=False,
                     action='store_true', help='create tessellation')
    prs.add_argument('--tess.render', default=False,
                     action='store_true', help='visualize tessellation')
    prs.add_argument('-u', '--umesh.active', default=False,
                     action='store_true', help='create unstructured mesh')
    prs.add_argument('--umesh.geom', default=True,
                     action='store_true', help='create geometry')
    prs.add_argument('--umesh.dwall', default=0.02,
                     help='wall thickness')
    prs.add_argument('--umesh.mesh', default=True,
                     action='store_true', help='perform meshing')
    prs.add_argument('--umesh.psize', default=0.025,
                     help='mesh size near geometry points')
    prs.add_argument('--umesh.esize', default=0.1,
                     help='mesh size near geometry edges')
    prs.add_argument('--umesh.csize', default=0.1,
                     help='mesh size in middle of geometry cells')
    prs.add_argument('--umesh.convert', default=0.1,
                     help='convert mesh to *.xml for fenics')
    prs.add_argument('-s', '--smesh.active', default=False,
                     action='store_true', help='create structured mesh')
    prs.add_argument('--smesh.render', default=False,
                     action='store_true', help='visualize structured mesh')
    prs.add_argument('--smesh.strut', default=0.6,
                     help='strut content')
    prs.add_argument('--smesh.por', default=0.94,
                     help='porosity')
    prs.add_argument('--smesh.isstrut', default=4,
                     help='initial guess of strut size parameter')
    prs.add_argument('--smesh.binarize', default=True,
                     action='store_true', help='binarize structure')
    prs.add_argument('--smesh.perbox', default=True,
                     action='store_true',
                     help='transform structure to periodic box')
    cfg = prs.parse_args(sys.argv[1:])
    generate(cfg)


def porOpt(vx):
    """Objective function.

    For finding size of box, which would give desired porosity.
    @param[in] vx Box size
    """
    filename = INPUTS["filename"]
    porosity = INPUTS["structured_grid_options"]["porosity"]
    vx = int(vx)
    vy = vx
    vz = vx
    if os.path.isfile(filename + 'Box.vtk'):
        os.remove(filename + 'Box.vtk')
    if not os.path.isfile(filename + 'Box.ply'):
        raise SystemError(".ply file is missing. Nothing to binarize.")
    os.system(
        "binvox -e -d {0:d} -rotz -rotx -rotz -rotz -t vtk ".format(vx)
        + filename + "Box.ply >binvox.out"
    )
    with open('binvox.out') as data_file:
        for line in data_file:
            if "counted" in line:
                solidVoxel, totalVoxel =\
                    [int(s) for s in line.split() if s.isdigit()]
                eps = 1 - solidVoxel / totalVoxel
                print("dimension: {0:4d}, porosity: {1:f}".format(vx, eps))
                return (eps - porosity)**2


def porfsOpt(x):
    """Objective function.

    For finding size of box, which would give desired porosity and
    strut content.
    @param[in] x Box size
    """
    global DEDGE
    filename = INPUTS["filename"]
    porosity = INPUTS["structured_grid_options"]["porosity"]
    strut_content = INPUTS["structured_grid_options"]["strut_content"]
    vx = int(x)
    vy = vx
    vz = vx
    if os.path.isfile(filename + 'Box.vtk'):
        os.remove(filename + 'Box.vtk')
    if not os.path.isfile(filename + 'Box.ply'):
        raise SystemError(".ply file is missing. Nothing to binarize.")
    os.system(
        "binvox -e -d {0:d} -rotz -rotx -rotz -rotz -t vtk ".format(vx)
        + filename + "Box.ply >binvox.out"
    )
    filenameIn = filename + "Box.vtk"
    filenameOut = filename + "Box-ascii.vtk"
    dx = dy = dz = INPUTS["packing_options"]["domain_size"]
    origin = [dx, dy, dz]
    spacing = [dx / vx, dy / vy, dz / vz]
    vtkconv.main(filenameIn, filenameOut, origin, spacing)
    f = open("foamreconstr.in", "w")
    f.write("0\n")
    f.write("1\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("{0:f}\n".format(DEDGE))
    f.write("{0:f}\n".format(1 - strut_content * (1 - porosity)))
    f.write("0\n")
    f.write("1\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("0\n")
    f.write("1\n")
    f.write("0\n")
    f.write("1\n")
    f.write("0\n")
    f.write(filename + "Box_structured\n")
    f.write(filename + "Box-ascii.vtk\n")
    f.write(filename + ".gnu\n")
    f.write("name\n")
    f.write("descriptors.txt" + "\n")
    f.write("parameters.txt" + "\n")
    f.close()
    os.system("./foamreconstr/foamreconstr")
    f = open("descriptors.txt", "r")
    eps = float(f.readline())
    fs = float(f.readline())
    f.close()
    f = open("parameters.txt", "r")
    DEDGE = float(f.readline())
    f.close()
    resid = ((eps - porosity) / porosity)**2
    print("dimension: {0:4d}, porosity: {1:f}".format(
        vx, eps) + ", strut content: {0:f}".format(fs))
    return resid


def periodic_box(filename, render_box):
    """Uses gmsh, vtk, and meshconv to move closed foam to periodic box."""
    dx = dy = dz = INPUTS["packing_options"]["domain_size"]
    # Convert .geo to .stl
    print(
        TERM.yellow +
        "Convert .geo to .stl" +
        TERM.normal
    )
    os.system("gmsh -n -2 -format stl " + filename + ".geo >gmsh.out")
    # Move to periodic box
    print(
        TERM.yellow +
        "Move to periodic box" +
        TERM.normal
    )
    xmin = 0
    ymin = 0
    zmin = 0
    periodicBox.main(
        filename + ".stl", filename + "Box.stl", xmin, ymin, zmin, dx, dy, dz,
        render_box
    )
    # Convert .stl to .ply
    print(
        TERM.yellow +
        "Convert .stl to .ply" +
        TERM.normal
    )
    os.system("meshconv " + filename + "Box.stl -c ply")


def binarize_box(filename, dx, dy, dz, porosity, strut_content):
    """Creates foam with desired porosity and strut content on structured grid."""
    # Binarize and save as .vtk
    if strut_content == 0:
        # Find the size of box, which would give desired porosity
        # This method is not optimal, since the solver doesn't know that the
        # function takes only integer arguments
        print(
            TERM.yellow +
            "Optimizing porosity" +
            TERM.normal
        )
        res = minimize_scalar(
            porOpt, bracket=[100, 120], method='Brent', tol=1e-2
        )
        vx = vy = vz = int(res.x)
        print('box size: {0:d}'.format(vx))
        print(
            TERM.yellow +
            "Creating and saving optimal foam" +
            TERM.normal
        )
        porOpt(vx)  # Call it with the optimized box size
        # Convert binary .vtk to ascii .vtk
        print(
            TERM.yellow +
            "Convert binary .vtk to ascii .vtk" +
            TERM.normal
        )
        origin = [dx, dy, dz]
        spacing = [dx / vx, dy / vy, dz / vz]
        vtkconv.main(filename + "Box.vtk", filename +
                     "_str.vtk", origin, spacing)
    else:
        print(
            TERM.yellow +
            "Optimizing porosity and strut content" +
            TERM.normal
        )
        res = minimize_scalar(
            porfsOpt, bracket=[150, 200], method='Brent', tol=1e-2
        )
        # res=minimize_scalar(
        #     porfsOpt,bounds=[200,250],method='bounded',tol=2e0
        # )
        vx = vy = vz = int(res.x)
        print('optimal box size: {0:d}'.format(vx))
        print(
            TERM.yellow +
            "Creating and saving optimal foam" +
            TERM.normal
        )
        if os.path.isfile(filename + 'Box.vtk'):
            os.remove(filename + 'Box.vtk')
        if not os.path.isfile(filename + 'Box.ply'):
            raise SystemError(".ply file is missing. Nothing to binarize.")
        os.system(
            "binvox -e -d {0:d}".format(vx) + " -rotz -rotx -rotz -rotz "
            + "-t vtk " + filename + "Box.ply >binvox.out"
        )
        origin = [dx, dy, dz]
        spacing = [dx / vx, dy / vy, dz / vz]
        vtkconv.main(filename + "Box.vtk", filename +
                     "Box-ascii.vtk", origin, spacing)
        f = open("foamreconstr.in", "w")
        f.write("0\n")
        f.write("1\n")
        f.write("0\n")
        f.write("0\n")
        f.write("1\n")
        f.write("0\n")
        f.write("{0:f}\n".format(DEDGE))
        f.write("{0:f}\n".format(1 - strut_content * (1 - porosity)))
        f.write("0\n")
        f.write("1\n")
        f.write("0\n")
        f.write("0\n")
        f.write("0\n")
        f.write("0\n")
        f.write("0\n")
        f.write("0\n")
        f.write("1\n")
        f.write("0\n")
        f.write("1\n")
        f.write("0\n")
        f.write(filename + "_str\n")
        f.write(filename + "Box-ascii.vtk\n")
        f.write(filename + ".gnu\n")
        f.write("name\n")
        f.write("descriptors.txt" + "\n")
        f.write("parameters.txt" + "\n")
        f.close()
        os.system("./foamreconstr/foamreconstr")


def mesh_domain(domain):
    """Mesh computational domain using Gmsh."""
    call = sp.Popen(['gmsh', '-3', '-v', '3', '-format', 'msh2', domain])
    call.wait()


def convert_mesh(input_mesh, output_mesh):
    """Convert mesh to xml using dolfin-convert."""
    call = sp.Popen(['dolfin-convert', input_mesh, output_mesh])
    call.wait()


def structured_grid(filename, dx, dy, dz, porosity, strut_content):
    """Creates foam discretized on structured grid."""
    if INPUTS["structured_grid_options"]["move_to_periodic_box"]:
        print(
            TERM.yellow +
            "Creating periodic box." +
            TERM.normal
        )
        periodic_box(
            INPUTS["filename"],
            INPUTS["structured_grid_options"]["render_box"])
    if INPUTS["structured_grid_options"]["binarize_box"]:
        print(
            TERM.yellow +
            "Meshing." +
            TERM.normal
        )
        binarize_box(filename, dx, dy, dz, porosity, strut_content)


def unstructured_grid(filename, wall_thickness, verbose):
    """Creates foam discretized on unstructured grid."""
    if INPUTS["unstructured_grid_options"]["create_geometry"]:
        geo_tools.main(filename,
                       wall_thickness,
                       [INPUTS["unstructured_grid_options"]["point_sizing"],
                        INPUTS["unstructured_grid_options"]["edge_sizing"],
                        INPUTS["unstructured_grid_options"]["cell_sizing"]],
                       verbose)
        shutil.copy(filename + "WallsBoxFixed.geo",
                    filename + "_uns.geo")
    if INPUTS["unstructured_grid_options"]["mesh_domain"]:
        mesh_domain(filename + "_uns.geo")
    if INPUTS["unstructured_grid_options"]["convert_mesh"]:
        convert_mesh(filename + "_uns.msh",
                     filename + "_uns.xml")


def main():
    """Main function.

    Executed when running the script from command line.
    """
    time_start = datetime.datetime.now()
    if INPUTS["packing"]:
        print(
            TERM.yellow +
            "Packing spheres." +
            TERM.normal
        )
        packing.pack_spheres(
            INPUTS["packing_options"]["shape"],
            INPUTS["packing_options"]["scale"],
            INPUTS["packing_options"]["number_of_cells"],
            INPUTS["packing_options"]["algorithm"])
    if INPUTS["tessellation"]:
        print(
            TERM.yellow +
            "Tessellating." +
            TERM.normal
        )
        tessellation.tessellate(
            INPUTS["filename"],
            INPUTS["packing_options"]["number_of_cells"],
            INPUTS["tessellation_options"]["visualize_tessellation"])
    if INPUTS["structured_grid"]:
        print(
            TERM.yellow +
            "Creating structured grid." +
            TERM.normal
        )
        structured_grid(
            INPUTS["filename"],
            INPUTS["packing_options"]["domain_size"],
            INPUTS["packing_options"]["domain_size"],
            INPUTS["packing_options"]["domain_size"],
            INPUTS["structured_grid_options"]["porosity"],
            INPUTS["structured_grid_options"]["strut_content"])
    if INPUTS["unstructured_grid"]:
        print(
            TERM.yellow +
            "Creating unstructured grid." +
            TERM.normal
        )
        unstructured_grid(
            INPUTS["filename"],
            INPUTS["unstructured_grid_options"]["wall_thickness"],
            ARGS['--verbose'])
    time_end = datetime.datetime.now()
    print("Foam created in: {}".format(time_end - time_start))
