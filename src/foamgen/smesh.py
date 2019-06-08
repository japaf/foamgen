"""@author: pavel.ferkl@gmail.com"""
from __future__ import division, print_function
import os
from scipy.optimize import minimize_scalar
from . import periodicBox
from . import vtkconv


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
    dx = dy = dz = cfg.smesh.dsize
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
    dx = dy = dz = cfg.smesh.dsize
    # Convert .geo to .stl
    print(
        term.yellow +
        "Convert .geo to .stl" +
        term.normal
    )
    os.system("gmsh -n -2 -format stl " + filename + ".geo >gmsh.out")
    # Move to periodic box
    print(
        term.yellow +
        "Move to periodic box" +
        term.normal
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
        term.yellow +
        "Convert .stl to .ply" +
        term.normal
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
            term.yellow +
            "Optimizing porosity" +
            term.normal
        )
        res = minimize_scalar(
            porOpt, bracket=[100, 120], method='Brent', tol=1e-2
        )
        vx = vy = vz = int(res.x)
        print('box size: {0:d}'.format(vx))
        print(
            term.yellow +
            "Creating and saving optimal foam" +
            term.normal
        )
        porOpt(vx)  # Call it with the optimized box size
        # Convert binary .vtk to ascii .vtk
        print(
            term.yellow +
            "Convert binary .vtk to ascii .vtk" +
            term.normal
        )
        origin = [dx, dy, dz]
        spacing = [dx / vx, dy / vy, dz / vz]
        vtkconv.main(filename + "Box.vtk", filename +
                     "_str.vtk", origin, spacing)
    else:
        print(
            term.yellow +
            "Optimizing porosity and strut content" +
            term.normal
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
            term.yellow +
            "Creating and saving optimal foam" +
            term.normal
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


def structured_grid(filename, dx, dy, dz, porosity, strut_content):
    """Creates foam discretized on structured grid."""
    if INPUTS["structured_grid_options"]["move_to_periodic_box"]:
        print(
            term.yellow +
            "Creating periodic box." +
            term.normal
        )
        periodic_box(
            INPUTS["filename"],
            INPUTS["structured_grid_options"]["render_box"])
    if INPUTS["structured_grid_options"]["binarize_box"]:
        print(
            term.yellow +
            "Meshing." +
            term.normal
        )
        binarize_box(filename, dx, dy, dz, porosity, strut_content)
