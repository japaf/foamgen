"""
Tessellation module
===================
:synopsis: Periodic domain weighted tessellation.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
.. moduleauthor:: Mohammad Marvi-Mashhadi <mohammad.marvi@imdea.org>
"""
import os
import subprocess as sp
import shlex as sx
import pandas as pd
from .geo_tools import read_geo, extract_data
from . import vtk_tools


def tessellate(fname, visualize, clean):
    """Use Laguerre tessellation to create dry foam.

    Uses `Neper <http://neper.sourceforge.net/>`_ for tessellation.
    ``*Packing.csv`` must exists.

    Args:
        fname (str): base filename
        visualize (bool): create picture of tessellation if True
        clean (bool): delete redundant files if True
    """
    number_of_cells = prep(fname)
    neper_tessellation(fname, number_of_cells)
    periodic_box(fname, 1, False)
    save_gnuplot(fname)
    if visualize:
        neper_visualize(fname)
    if clean:
        clean_files()


def prep(fname):
    """Prepare input files for Neper.

    Creates ``centers.txt`` and ``rads.txt`` files.

    Args:
        fname (str): base filename

    Returns:
        int: number of cells
    """
    dtf = pd.read_csv(fname + 'Packing.csv')
    dtf['r'] = dtf['d'] / 2
    dtf[['x', 'y', 'z']].to_csv('centers.txt', sep='\t', header=None,
                                index=None)
    dtf[['r']].to_csv('rads.txt', sep='\t', header=None, index=None)
    return len(dtf)


def neper_tessellation(fname, number_of_cells, rve_size=1):
    """Run Neper tessellation module.

    Neper regularization is not available for periodic tessellations. Requires
    ``centers.txt`` and ``rads.txt`` files.

    Args:
        fname (str): base filename
        number_of_cells (int): number of cells
        rve_size (float, optional): domain size
    """
    command = "neper -T \
        -n {0:d} \
        -domain 'cube({1:d},{1:d},{1:d})' \
        -periodicity x,y,z \
        -morpho voronoi \
        -morphooptiini 'coo:file(centers.txt),weight:file(rads.txt)' \
        -o {2}Tessellation -format tess,geo \
        -statcell vol -statedge length -statface area \
        -statver x".format(number_of_cells, rve_size, fname)
    sp.Popen(sx.split(command)).wait()


def neper_visualize(fname):
    """Run Neper visualization module.

    Requires POV-Ray package. Requires ``*Tessellation.tess`` and ``rads.txt``
    files.

    Args:
        fname (str): base filename
    """
    command = "neper -V {0}Tessellation.tess -datacellcol ori \
        -datacelltrs 0.5 -showseed all -dataseedrad @rads.txt \
        -dataseedtrs 1.0 -print {0}Tessellation".format(fname)
    sp.Popen(sx.split(command))


def save_gnuplot(fname):
    """Save tessellation in gnuplot format.

    Requires ``*Tessellation.tess`` file. Creates ``*Tessellation.gnu`` file.

    Args:
        fname (str): base filename
    """
    sdat = read_geo(fname + "Tessellation.geo")
    edat = extract_data(sdat)
    point = edat["point"]
    line = edat["line"]
    with open('{0}Tessellation.gnu'.format(fname), 'w') as flp:
        for pidx in line.values():
            flp.write('{0} {1} {2}\n'.format(
                point[pidx[0]][0], point[pidx[0]][1], point[pidx[0]][2]))
            flp.write('{0} {1} {2}\n\n\n'.format(
                point[pidx[1]][0], point[pidx[1]][1], point[pidx[1]][2]))


def periodic_box(fname, dsize, render):
    """Uses gmsh and vtk to move closed foam to periodic box.

    Requires ``*Tessellation.geo`` file. Creates ``*TessellationBox.stl`` file.

    Args:
        fname (str): base filename
        dsize (float): box size
        render (bool): render scene if True
    """
    geo_to_stl(fname + "Tessellation.geo")
    vtk_tools.stl_to_periodic_box(
        fname + "Tessellation.stl", fname + "TessellationBox.stl", [0, 0, 0],
        [dsize, dsize, dsize], render
    )


def geo_to_stl(fin):
    """Convert ``*.geo`` file to ``*.stl`` file

    Uses ``gmsh``.

    Args:
        fin (str): input filename
    """
    print("Converting .geo to .stl")
    cmd = sx.split("gmsh -n -2 -v 3 -format stl " + fin)
    sp.Popen(cmd).wait()


def clean_files():
    """Delete unnecessary files."""
    flist = [
        'centers.txt',
        'rads.txt',
        'generation.conf',
        'packing_init.xyzd',
        'packing.nfo',
        'packing_prev.xyzd',
        'packing.xyzd',
    ]
    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)
