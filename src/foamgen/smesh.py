"""
Structured meshing module
=========================
:synopsis: Create structured VTK mesh.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from __future__ import division, print_function
import os
import shutil
import subprocess as sp
import shlex
from scipy.optimize import root_scalar
from . import vtk_tools


def structured_mesh(fname, porosity, strut_content):
    """Create foam discretized on structured cartesian mesh.

    Creates foam with desired porosity and strut content. ``root_scalar`` from
    scipy is used for root finding. This method is not optimal, since the
    solver doesn't know that the function takes only integer arguments.

    Ultimate output is the ``*SMesh.vtk`` file.

    Args:
        fname (str): base filename
        porosity (float): target foam porosity
        strut_content (float): target foam strut content
    """
    dsize = 1
    # Binarize and save as .vtk
    if strut_content == 0:
        print("Optimizing porosity")
        res = root_scalar(por_res, args=(fname, porosity), x0=100, x1=120,
                          method='secant', rtol=1e-2)
        delta = int(res.root)
        print('box size: {0:d}'.format(delta))
        print("Creating and saving optimal foam")
        # Call it with the optimized box size
        por_res(delta, fname, porosity)
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
        # Call it with the optimized box size
        por_fs_res(delta, fname, dsize, porosity, strut_content)
    clean_files()


def por_res(delta, fname, porosity):
    """Residual function for finding target porosity.

    Adjusts the size of the box, in which the foam is binarized. Bigger box
    leads to thinner walls and higher porosity.

    :func:`voxelize_morphology` is used to create walls.

    Args:
        delta (float): box size in voxels
        fname (str): base filename
        porosity (float): target porosity

    Returns:
        float: squared difference between target and actual porosity
    """
    delta = int(delta)
    out = voxelize_morphology(fname, delta)
    for line in out:
        if "counted" in line:
            solid_voxel, total_voxel =\
                [int(s) for s in line.split() if s.isdigit()]
            break
    eps = 1 - solid_voxel / total_voxel
    print("dimension: {0:4d}, porosity: {1:f}".format(delta, eps))
    return (eps - porosity)**2


def por_fs_res(delta, fname, dsize, porosity, strut_content):
    """Residual function for finding target porosity and strut content.

    Adjusts the size of the box, in which the foam is binarized and strut size
    parameter. Bigger box leads to thinner walls and higher porosity. Higher
    strut size parameter leads to higher strut content.

    :func:`voxelize_morphology` is used to create walls.
    ``foamreconstr`` program is used to create struts and optimize strut
    content.

    Requires ``*Tessellation.gnu`` file.

    Args:
        delta (float): box size in voxels
        fname (str): base filename
        dsize (float): box size
        porosity (float): target foam porosity
        strut_content (float): target foam strut content

    Returns:
        float: squared difference between target and actual porosity
    """
    delta = int(delta)
    voxelize_morphology(fname, delta)
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
    with open("descriptors.txt", "r") as fhl:
        eps = float(fhl.readline())
        fstr = float(fhl.readline())
    print("dimension: {0:4d}, porosity: {1:f}".format(delta, eps) +
          ", strut content: {0:f}".format(fstr))
    return (eps - porosity)**2


def voxelize_morphology(fname, delta):
    """Create foam on equidistant cartesian mesh.

    Requires ``*TessellationBox.stl`` file. Creates ``*SMesh.vtk`` file.

    Args:
        fname (str): base filename
        delta (float): box size

    Returns:
        str: binvox stdout
    """
    if os.path.isfile(fname + 'SMesh.vtk'):
        os.remove(fname + 'SMesh.vtk')
    if not os.path.isfile(fname + 'TessellationBox.stl'):
        raise Exception(".stl file is missing. Nothing to binarize.")
    shutil.copy2(fname + 'TessellationBox.stl', fname + 'SMesh.stl')
    cmd = shlex.split(
        "binvox -e -d {0:d} -t vtk ".format(delta) + fname + "SMesh.stl"
    )
    call = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    out, _ = call.communicate()
    out = out.decode().splitlines()
    if os.path.isfile(fname + 'SMesh.stl'):
        os.unlink(fname + 'SMesh.stl')
    return out


def clean_files():
    """Delete unnecessary files."""
    flist = [
        'descriptors.txt',
        'parameters.txt',
        'foamreconstr.in',
    ]
    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)
