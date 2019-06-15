"""
@file       tessellation.py
@namespace  FoamConstruction.tessellation
@ingroup    mod_foamConstruction
@brief      Tesselation.
@author     Mohammad Marvi-Mashhadi
@author     Pavel Ferkl
@copyright  2014-2016, MoDeNa Project. GNU Public License.
@details
Prepares representative volume element (RVE) of foam using Laguerre
tessellation.
Uses Neper 3.
"""
import os
import subprocess as sp
import shlex as sx
import pandas as pd
from .geo_tools import read_geo, extract_data


def tessellate(fname, number_of_cells, visualize, gnuplot=True):
    """
    Use Laguerre tessellation from Neper to create dry foam. Uses
    FilePacking.csv as input file.
    """
    prep(fname)
    neper_tessellation(fname, number_of_cells)
    if visualize:
        neper_visualize(fname)
    if gnuplot:
        save_gnuplot(fname)
    clean()


def prep(fname):
    """Prepare input files for Neper."""
    dtf = pd.read_csv(fname + 'Packing.csv')
    dtf['r'] = dtf['d'] / 2
    dtf[['x', 'y', 'z']].to_csv('centers.txt', sep='\t', header=None,
                                index=None)
    dtf[['r']].to_csv('rads.txt', sep='\t', header=None, index=None)


def neper_tessellation(fname, number_of_cells, rve_size=1):
    """
    Use Neper to perform tessellation. Note: Neper regularization is not
    available for periodic tessellations.
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
    """Use neper to visualize tessellation. Requires Pov-Ray package."""
    command = "neper -V {0}Tessellation.tess -datacellcol ori \
        -datacelltrs 0.5 -showseed all -dataseedrad @rads.txt \
        -dataseedtrs 1.0 -print {0}Tessellation".format(fname)
    sp.Popen(sx.split(command))


def save_gnuplot(fname):
    """Save tessellation in gnuplot format."""
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


def clean():
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
