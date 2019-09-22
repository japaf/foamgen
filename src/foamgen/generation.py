"""
Generation module
=================
:synopsis: Organizes creation of foam morphology.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from __future__ import division, print_function
import sys
import datetime
import logging
import yaml
import munch
import jsonargparse as jp
from blessings import Terminal
from . import packing
from . import tessellation
from . import morphology
from . import umesh
from . import smesh


def parse_cli_and_generate():
    """Parse CLI arguments and call :func:`generate` function.

    Parsing is done using `jsonargparse
    <https://omni-us.github.io/jsonargparse/>`_. This function is called by the
    ``foamgen`` executable.
    """
    prs = jp.ArgumentParser(
        prog='foamgen',
        error_handler=jp.usage_and_exit_error_handler,
        description='Generate foam morphology.')
    prs.add_argument('-v', '--verbose', default=False,
                     action='store_true', help='verbose output')
    prs.add_argument('-c', '--config', action=jp.ActionConfigFile,
                     help='name of config file')
    prs.add_argument('-f', '--filename', default='Foam',
                     help='base filename')
    prs.add_argument('-p', '--pack.active', default=False,
                     action='store_true', help='create sphere packing')
    prs.add_argument('--pack.ncells', default=27, type=int,
                     help='number of cells')
    prs.add_argument('--pack.shape', default=0.2, type=float,
                     help='sphere size distribution shape factor')
    prs.add_argument('--pack.scale', default=0.35, type=float,
                     help='sphere size distribution scale factor')
    prs.add_argument('--pack.alg', default='fba',
                     help='packing algorithm')
    prs.add_argument('--pack.render', default=False,
                     action='store_true', help='visualize packing')
    prs.add_argument('--pack.clean', default=True, action='store_true',
                     help='clean redundant files')
    prs.add_argument('--pack.maxit', default=5, type=int,
                     help='maximum number of iterations')
    prs.add_argument('-t', '--tess.active', default=False,
                     action='store_true', help='create tessellation')
    prs.add_argument('--tess.render', default=False,
                     action='store_true', help='visualize tessellation')
    prs.add_argument('--tess.clean', default=True, action='store_true',
                     help='clean redundant files')
    prs.add_argument('-m', '--morph.active', default=False,
                     action='store_true', help='create final morphology')
    prs.add_argument('--morph.dwall', default=0.02, type=float,
                     help='wall thickness')
    prs.add_argument('--morph.clean', default=True, action='store_true',
                     help='clean redundant files')
    prs.add_argument('-u', '--umesh.active', default=False,
                     action='store_true', help='create unstructured mesh')
    prs.add_argument('--umesh.psize', default=0.025, type=float,
                     help='mesh size near geometry points')
    prs.add_argument('--umesh.esize', default=0.1, type=float,
                     help='mesh size near geometry edges')
    prs.add_argument('--umesh.csize', default=0.1, type=float,
                     help='mesh size in middle of geometry cells')
    prs.add_argument('--umesh.convert', default=True, action='store_true',
                     help='convert mesh to *.xml for fenics')
    prs.add_argument('-s', '--smesh.active', default=False,
                     action='store_true', help='create structured mesh')
    prs.add_argument('--smesh.strut', default=0.6, type=float,
                     help='strut content')
    prs.add_argument('--smesh.por', default=0.94, type=float,
                     help='porosity')
    prs.add_argument('--smesh.isstrut', default=4, type=int,
                     help='initial guess of strut size parameter')
    prs.add_argument('--smesh.binarize', default=True,
                     action='store_true', help='binarize structure')
    prs.add_argument('--smesh.perbox', default=True,
                     action='store_true',
                     help='transform structure to periodic box')
    cfg = prs.parse_args(sys.argv[1:])
    generate(cfg)


def parse_config_file(fname):
    """Parse configurational file.

    Parsed options can be accessed as arguments of the returned object. For
    more information see `Munch <https://github.com/Infinidat/munch>`_.

    Args:
        fname (str): config filename

    Returns:
        Munch: parsed config file
    """
    with open(fname, 'r') as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return munch.munchify(cfg)


def generate(cfg):
    """Generate foam morphology.

    Args:
        cfg (Namespace): parsed inputs
    """
    # Creates terminal for colour output
    term = Terminal()
    time_start = datetime.datetime.now()
    # switch off matplotlib DEBUG messages
    mpl_logger = logging.getLogger('matplotlib')
    mpl_logger.setLevel(logging.WARNING)
    if cfg.pack.active:
        print(term.yellow + "Packing spheres." + term.normal)
        packing.pack_spheres(cfg.filename,
                             cfg.pack.shape,
                             cfg.pack.scale,
                             cfg.pack.ncells,
                             cfg.pack.alg,
                             cfg.pack.maxit,
                             cfg.pack.render,
                             cfg.pack.clean)
    if cfg.tess.active:
        print(term.yellow + "Tessellating." + term.normal)
        tessellation.tessellate(cfg.filename,
                                cfg.tess.render,
                                cfg.tess.clean)
    if cfg.morph.active:
        print(term.yellow + "Creating final morphology." + term.normal)
        morphology.make_walls(cfg.filename,
                              cfg.morph.dwall,
                              cfg.morph.clean)
    if cfg.umesh.active:
        print(term.yellow + "Creating unstructured mesh." + term.normal)
        umesh.unstructured_mesh(cfg.filename,
                                [cfg.umesh.psize,
                                 cfg.umesh.esize,
                                 cfg.umesh.csize],
                                cfg.umesh.convert)
    if cfg.smesh.active:
        print(term.yellow + "Creating structured mesh." + term.normal)
        smesh.structured_mesh(cfg.filename,
                              cfg.smesh.por,
                              cfg.smesh.strut)
    time_end = datetime.datetime.now()
    print("Foam created in: {}".format(time_end - time_start))
