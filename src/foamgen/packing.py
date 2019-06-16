"""
Packing module
==============
:synopsis: Prepares packed spheres for tessellation.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
.. moduleauthor:: Mohammad Marvi-Mashhadi <mohammad.marvi@imdea.org>
"""
from __future__ import division, print_function
import struct
import os
import time
import random
import subprocess
import numpy as np
import pandas as pd
from scipy.stats import lognorm
import matplotlib.pyplot as plt
import spack


def simple_packing(diam):
    """Simple and fast algorithm for packing.

    Often leads to overlapping spheres. Can lead to infinite loop, thus it
    raises Exception after 10 s. Use of this algorithm at this stage is
    discouraged.

    Args:
        diam (ndarray): array of sphere diameters

    Returns:
        DataFrame: center positions and diameters of spheres

    Raises:
        Exception: when running for more than 10 s
    """
    number_of_cells = len(diam)
    rads = diam / 2
    rads.sort()
    vol = sum((2 * rads)**3)
    vol = vol * 1.40
    lch = vol**(1.00 / 3.00)
    centers = np.zeros((number_of_cells, 3))
    finished = False
    while not finished:
        j = -1
        timeout = time.time() + 10
        while number_of_cells >= j:
            if time.time() > timeout:
                raise Exception('Timed out!')
            j = j + 1
            if j == number_of_cells:
                finished = True
                break
            # pick new coordinates
            pick_x = lch * random.random()
            pick_y = lch * random.random()
            pick_z = lch * random.random()
            while (rads[j] < pick_x <= lch - rads[j] and
                   rads[j] < pick_y <= lch - rads[j] and
                   rads[j] < pick_z <= lch - rads[j]):
                pick_x = lch * random.random()
                pick_y = lch * random.random()
                pick_z = lch * random.random()
            centers[j][0] = pick_x
            centers[j][1] = pick_y
            centers[j][2] = pick_z
            # new sphere must not overlap with already existing sphere
            if j > 0:
                for i in range(0, j):
                    if ((((((pick_x - centers[i][0])**2) +
                           ((pick_y - centers[i][1])**2) +
                           ((pick_z - centers[i][2])**2))**0.5) -
                         (rads[j] + rads[i])) < 0) and i != j:
                        centers[j][0], centers[j][0], centers[j][0] = 0, 0, 0
                        j = j - 1
                        break
    dtf = pd.DataFrame(centers, columns=('x', 'y', 'z'))
    dtf['d'] = 2 * rads
    return dtf


def create_input(npart, domain=1.0):
    """Create input file for packing-generation program.

    Function creates ``generation.conf`` file with some default inputs.

    Args:
        npart (int): number of spheres
        domain (float, optional): size of domain
    """
    txt = """Particles count: {0}
Packing size: {1} {1} {1}
Generation start: 1
Seed: 341
Steps to write: 1000
Boundaries mode: 1
Contraction rate: 1.328910e-005
    """.format(npart, domain)
    with open('generation.conf', 'w') as fout:
        fout.write(txt)


def make_csd(shape, scale, npart):
    """Create cell size distribution and save it to file.

    Log-normal distribution from scipy is used. Creates ``diameters.txt`` file
    with sphere diameters.

    Args:
        shape (float): shape size parameter of log-normal distribution
        scale (float): scale size parameter of log-normal distribution
        npart (int): number of spheres

    Returns:
        ndarray: array of sphere diameters
    """
    if shape == 0:
        diam = [scale + 0 * x for x in range(npart)]
    else:
        diam = lognorm.rvs(shape, scale=scale, size=npart)
    with open('diameters.txt', 'w') as fout:
        for rad in diam:
            fout.write('{0}\n'.format(rad))
    return diam


def save_csd(fname, diam, shape, scale, show_plot=False):
    """Save cell size distribution plot.

    Creates files ``*.Packing_histogram.png`` and ``*.Packing_histogram.pdf``
    with cell size distribution histogram and continual probability density
    function.

    Args:
        fname (str): base filename
        diam (ndarray): array of sphere diameters
        shape (float): shape size parameter of log-normal distribution
        scale (float): scale size parameter of log-normal distribution
        show_plot (bool, optional): create window with plot
    """
    if shape == 0:
        xpos = np.linspace(scale / 2, scale * 2, 100)
    else:
        xpos = np.linspace(lognorm.ppf(0.01, shape, scale=scale),
                           lognorm.ppf(0.99, shape, scale=scale), 100)
    plt.figure(figsize=(12, 8))
    plt.rcParams.update({'font.size': 16})
    plt.plot(xpos, lognorm.pdf(xpos, shape, scale=scale), lw=3, label='input')
    plt.hist(diam, density=True, label='spheres')
    plt.grid()
    plt.xlabel('Size')
    plt.ylabel('Probability density function')
    plt.legend()
    plt.savefig(fname + 'Packing_histogram.png', dpi=300)
    plt.savefig(fname + 'Packing_histogram.pdf')
    if show_plot:
        plt.show()


def read_results():
    """Reads results of packing algorithm.

    Packing results are read from ``packing.nfo`` and ``packing.xyzd`` files.

    Returns:
        DataFrame: center positions and diameters of spheres
    """
    with open("packing.nfo", "r") as fin:
        fin.readline()
        fin.readline()
        por_theory = float(fin.readline().split()[2])
        por_final = float(fin.readline().split()[2])
        print('Theoretical porosity:', por_theory)
        print('Final porosity:', por_final)
    data = pd.DataFrame(columns=('x', 'y', 'z', 'd'))
    with open("packing.xyzd", "rb") as fin:
        btxt = fin.read()
        txt = list(struct.unpack("<" + "d" * (len(btxt) // 8), btxt))
        data = pd.DataFrame(np.reshape(txt, (-1, 4)),
                            columns=('x', 'y', 'z', 'd'))
    data['d'] = data['d'] * ((1 - por_final) / (1 - por_theory))**(1 / 3)
    return data


def render_packing(fname, data, domain=1.0, pixels=1000):
    """Save picture of packed domain.

    Uses `spack <https://pyspack.readthedocs.io/en/latest/>`_. Creates
    ``*Packing.png`` file.

    Args:
        fname (str): base filename
        data (DataFrame): center positions and diameters of spheres
        domain (float, optional): size of domain
        pixels (int, optional): picture resolution
    """
    pack = spack.Packing(data[['x', 'y', 'z']], data['d'], L=domain)
    print(pack.contacts())
    scene = pack.scene(rot=np.pi / 4, camera_height=0.5,
                       camera_dist=2.5e1, angle=4, cmap='autumn',
                       floater_color=None)
    scene.render(fname + 'Packing.png', width=pixels,
                 height=pixels, antialiasing=0.0001)


def generate_structure(flag):
    """Runs the packing algorithm.

    ``PackingGeneration.exe`` must exist. ``generation.conf`` must exist.

    Args:
        flag (str): argument to be passed to packing-generation program
    """
    if os.path.isfile("packing.nfo"):
        os.remove("packing.nfo")
    subprocess.Popen(['PackingGeneration.exe', flag]).wait()


def clean_files():
    """Delete unnecessary files."""
    flist = [
        'contraction_energies.txt',
        'diameters.txt',
        'generation.conf',
        'packing_init.xyzd',
        'packing.nfo',
        'packing_prev.xyzd',
        'packing.xyzd',
    ]
    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)


def pack_spheres(fname, shape, scale, number_of_cells, algorithm, maxit,
                 render, clean):
    """Packs spheres into periodic domain.

    Creates file ending ``Packing.csv`` with sphere centers and radii. Simple
    model is implemented directly, other algorithms use Vasili Baranov's `code
    <https://github.com/VasiliBaranov/packing-generation>`_.

    Args:
        fname (str): base filename
        shape (float): shape size parameter of log-normal distribution
        scale (float): scale size parameter of log-normal distribution
        number_of_cells (int): number of spheres
        algorithm (str): name of packing algorithm
        maxit (int): number of tries for packing algorithm
        render (bool): save picture of packing if True
        clean (bool): delete redundant files if True

    Raises:
        Exception: when maximum number of iterations was reached
    """
    if algorithm == 'simple':
        diam = make_csd(shape, scale, number_of_cells)
        data = simple_packing(diam)
    else:
        create_input(number_of_cells)
        for i in range(maxit):
            print('Iteration: {}'.format(i + 1))
            diam = make_csd(shape, scale, number_of_cells)
            generate_structure('-' + algorithm)
            if os.path.isfile("packing.nfo"):
                break
        if not os.path.isfile("packing.nfo"):
            raise Exception(
                'Packing algorithm failed. ' +
                'Try to change number of particles or size distribution.')
        data = read_results()
    save_csd(fname, diam, shape, scale)
    data.to_csv(fname + 'Packing.csv', index=None)
    if render:
        render_packing(fname, data)
    if clean:
        clean_files()
