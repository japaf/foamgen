"""@author: pavel.ferkl@gmail.com"""
from __future__ import division, print_function
import os
import shutil
import subprocess as sp
import shlex
from scipy.optimize import minimize_scalar, root_scalar
from . import vtk_tools


def structured_mesh(fname, dsize, porosity, strut_content, render):
    """Creates foam discretized on structured cartesian mesh.

    Args:
        fname (str): base filename
        dsize (float): box size
        porosity (float): target foam porosity
        strut_content (float): target foam strut content
        render (bool): render scene if True
    """
    periodic_box(fname, dsize, render)
    cartesian_mesh(fname, dsize, porosity, strut_content)


def periodic_box(fname, dsize, render):
    """Uses gmsh and vtk to move closed foam to periodic box.

    Input is ``*Tessellation.geo`` file and output is ``*Morphology.ply`` file.

    Args:
        fname (str): base filename
        dsize (float): box size
        render (bool): render scene if True
    """
    geo_to_stl(fname + "Tessellation.geo")
    vtk_tools.stl_to_periodic_box(
        fname + "Tessellation.stl", fname + "Morphology.ply", [0, 0, 0],
        [dsize, dsize, dsize], render
    )


def geo_to_stl(fin):
    """Convert ``*.geo`` file to ``*.stl`` file

    Uses ``gmsh``.

    Args:
        fin (str): input filename
    """
    print("Converting .geo to .stl")
    cmd = shlex.split("gmsh -n -2 -format stl " + fin)
    sp.Popen(cmd).wait()


def cartesian_mesh(fname, dsize, porosity, strut_content):
    """Create foam with desired porosity and strut content.

    Foam is created directly on equidistant cartesian mesh. ``root_scalar``
    from scipy is used for root finding.
    """
    # Binarize and save as .vtk
    if strut_content == 0:
        # Find the size of box, which would give desired porosity
        # This method is not optimal, since the solver doesn't know that the
        # function takes only integer arguments
        print("Optimizing porosity")
        # res = minimize_scalar(
        #     por_res, bracket=[100, 120], method='Brent', tol=1e-2
        # )
        res = root_scalar(por_res, args=(fname, porosity), x0=100, x1=120,
                          method='secant', rtol=1e-2)
        delta = int(res.root)
        print('box size: {0:d}'.format(delta))
        print("Creating and saving optimal foam")
        por_res(delta, fname, porosity)  # Call it with the optimized box size
        # Convert binary .vtk to ascii .vtk
        print("Convert binary .vtk to ascii .vtk")
        origin = [0, 0, 0]
        spacing = [dsize / delta, dsize / delta, dsize / delta]
        vtk_tools.vtk_bin_to_ascii(fname + "SMesh.vtk", fname + "SMesh.vtk",
                                   origin, spacing)
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
        if os.path.isfile(fname + 'Box.vtk'):
            os.remove(fname + 'Box.vtk')
        if not os.path.isfile(fname + 'Box.ply'):
            raise SystemError(".ply file is missing. Nothing to binarize.")
        os.system(
            "binvox -e -d {0:d}".format(vx) + " -rotz -rotx -rotz -rotz "
            + "-t vtk " + fname + "Box.ply >binvox.out"
        )
        origin = [dx, dy, dz]
        spacing = [dx / vx, dy / vy, dz / vz]
        vtkconv.main(fname + "Box.vtk", fname +
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
        f.write(fname + "_str\n")
        f.write(fname + "Box-ascii.vtk\n")
        f.write(fname + ".gnu\n")
        f.write("name\n")
        f.write("descriptors.txt" + "\n")
        f.write("parameters.txt" + "\n")
        f.close()
        os.system("./foamreconstr/foamreconstr")


def por_res(delta, fname, porosity):
    """Residual function for finding target porosity.

    Adjusts the size of the box, in which the foam is binarized. Bigger box
    leads to thinner walls and higher porosity.

    ``binvox`` is used for binarization of the morphology.

    Box size can in fact only be integer (amount of voxels).

    Args:
        delta (float): box size
        fname (str): base filename
        porosity (float): target porosity

    Returns:
        float: squared difference between target and actual porosity
    """
    delta = int(delta)
    if os.path.isfile(fname + 'SMesh.vtk'):
        os.remove(fname + 'SMesh.vtk')
    if not os.path.isfile(fname + 'Morphology.ply'):
        raise Exception(".ply file is missing. Nothing to binarize.")
    shutil.copy2(fname + 'Morphology.ply', fname + 'SMesh.ply')
    cmd = shlex.split(
        "binvox -e -d {0:d} -t vtk ".format(delta) + fname + "SMesh.ply"
    )
    # cmd = shlex.split(
    #     "binvox -e -d {0:d} -rotz -rotx -rotz -rotz -t vtk ".format(delta)
    #     + fname + "SMesh.ply"
    # )
    call = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    out, _ = call.communicate()
    out = out.decode().splitlines()
    if os.path.isfile(fname + 'SMesh.ply'):
        os.unlink(fname + 'SMesh.ply')
    for line in out:
        if "counted" in line:
            solid_voxel, total_voxel =\
                [int(s) for s in line.split() if s.isdigit()]
            break
    eps = 1 - solid_voxel / total_voxel
    print("dimension: {0:4d}, porosity: {1:f}".format(delta, eps))
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
