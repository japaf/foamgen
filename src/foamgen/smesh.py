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
        fname + "Tessellation.stl", fname + "Morphology.stl", [0, 0, 0],
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
        print("Optimizing porosity and strut content")
        res = root_scalar(por_fs_res,
                          args=(fname, dsize, porosity, strut_content),
                          x0=100, x1=120, method='secant', rtol=1e-2)
        delta = int(res.root)
        print('box size: {0:d}'.format(delta))
        print("Creating and saving optimal foam")
        if os.path.isfile(fname + 'SMesh.vtk'):
            os.remove(fname + 'SMesh.vtk')
        if not os.path.isfile(fname + 'Morphology.stl'):
            raise Exception(".stl file is missing. Nothing to binarize.")
        shutil.copy2(fname + 'Morphology.stl', fname + 'SMesh.stl')
        cmd = shlex.split(
            "binvox -e -d {0:d} -t vtk ".format(delta) + fname + "SMesh.stl"
        )
        sp.Popen(cmd).wait()
        if os.path.isfile(fname + 'SMesh.stl'):
            os.unlink(fname + 'SMesh.stl')
        origin = [0, 0, 0]
        spacing = [dsize / delta, dsize / delta, dsize / delta]
        vtk_tools.vtk_bin_to_ascii(fname + "SMesh.vtk", fname + "SMesh.vtk",
                                   origin, spacing)
        try:
            with open("parameters.txt", "r") as fhl:
                dedge = float(fhl.readline())
        except FileNotFoundError:
            dedge = 2
        with open("foamreconstr.in", "w") as fhl:
            fhl.write("0\n")
            fhl.write("1\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("1\n")
            fhl.write("0\n")
            fhl.write("{0:f}\n".format(dedge))
            fhl.write("{0:f}\n".format(1 - strut_content * (1 - porosity)))
            fhl.write("0\n")
            fhl.write("1\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("0\n")
            fhl.write("1\n")
            fhl.write("0\n")
            fhl.write("1\n")
            fhl.write("0\n")
            fhl.write(fname + "SMesh\n")
            fhl.write(fname + "SMesh.vtk\n")
            fhl.write(fname + "Tessellation.gnu\n")
            fhl.write("name\n")
            fhl.write("descriptors.txt" + "\n")
            fhl.write("parameters.txt" + "\n")
        sp.Popen("foamreconstr").wait()


def por_res(delta, fname, porosity):
    """Residual function for finding target porosity.

    Adjusts the size of the box, in which the foam is binarized. Bigger box
    leads to thinner walls and higher porosity.

    ``binvox`` is used for binarization of the morphology.

    Box size can in fact only be integer (amount of voxels).

    Requires ``*Morphology.stl`` file. Creates ``*SMesh.vtk`` file.

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
    if not os.path.isfile(fname + 'Morphology.stl'):
        raise Exception(".stl file is missing. Nothing to binarize.")
    shutil.copy2(fname + 'Morphology.stl', fname + 'SMesh.stl')
    cmd = shlex.split(
        "binvox -e -d {0:d} -t vtk ".format(delta) + fname + "SMesh.stl"
    )
    call = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    out, _ = call.communicate()
    out = out.decode().splitlines()
    if os.path.isfile(fname + 'SMesh.stl'):
        os.unlink(fname + 'SMesh.stl')
    for line in out:
        if "counted" in line:
            solid_voxel, total_voxel =\
                [int(s) for s in line.split() if s.isdigit()]
            break
    eps = 1 - solid_voxel / total_voxel
    print("dimension: {0:4d}, porosity: {1:f}".format(delta, eps))
    return (eps - porosity)**2


def por_fs_res(delta, fname, dsize, porosity, strut_content):
    """Objective function.

    For finding size of box, which would give desired porosity and
    strut content.
    @param[in] x Box size
    """
    delta = int(delta)
    if os.path.isfile(fname + 'SMesh.vtk'):
        os.remove(fname + 'SMesh.vtk')
    if not os.path.isfile(fname + 'Morphology.stl'):
        raise Exception(".stl file is missing. Nothing to binarize.")
    shutil.copy2(fname + 'Morphology.stl', fname + 'SMesh.stl')
    cmd = shlex.split(
        "binvox -e -d {0:d} -t vtk ".format(delta) + fname + "SMesh.stl"
    )
    sp.Popen(cmd).wait()
    if os.path.isfile(fname + 'SMesh.stl'):
        os.unlink(fname + 'SMesh.stl')
    origin = [0, 0, 0]
    spacing = [dsize / delta, dsize / delta, dsize / delta]
    vtk_tools.vtk_bin_to_ascii(fname + "SMesh.vtk", fname + "SMesh.vtk",
                               origin, spacing)
    try:
        with open("parameters.txt", "r") as fhl:
            dedge = float(fhl.readline())
    except FileNotFoundError:
        dedge = 2
    with open("foamreconstr.in", "w") as fhl:
        fhl.write("0\n")
        fhl.write("1\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("{0:f}\n".format(dedge))
        fhl.write("{0:f}\n".format(1 - strut_content * (1 - porosity)))
        fhl.write("0\n")
        fhl.write("1\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("0\n")
        fhl.write("1\n")
        fhl.write("0\n")
        fhl.write("1\n")
        fhl.write("0\n")
        fhl.write(fname + "SMesh\n")
        fhl.write(fname + "SMesh.vtk\n")
        fhl.write(fname + "Tessellation.gnu\n")
        fhl.write("name\n")
        fhl.write("descriptors.txt" + "\n")
        fhl.write("parameters.txt" + "\n")
    sp.Popen("foamreconstr").wait()
    with open("descriptors.txt", "r") as fhl:
        eps = float(fhl.readline())
        fstr = float(fhl.readline())
    print("dimension: {0:4d}, porosity: {1:f}".format(
        delta, eps) + ", strut content: {0:f}".format(fstr))
    return (eps - porosity)**2
