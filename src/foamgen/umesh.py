"""
Unstructured meshing module
===========================
:synopsis: Create unstructured tetrahedral mesh.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from __future__ import print_function
import subprocess as sp
from . import geo_tools


def unstructured_mesh(fname, sizing, convert):
    """Create unstructured mesh.

    Optionally, convert mesh to ``*.xml`` format.

    Args:
        fname (str): base filename
        sizing (list): mesh size near points, edges and in cells
        convert (bool): convert mesh to fenics format if True
    """
    geo_tools.prep_mesh_config(
        fname + "Morphology.geo", fname + "UMesh.geo", sizing)
    mesh_domain(fname + "UMesh.geo")
    if convert:
        convert_mesh(fname + "UMesh.msh", fname + "UMesh.xml")


def mesh_domain(fname):
    """Mesh computational domain using Gmsh.

    Save mesh in old ``msh2`` format for denics compatibility.

    Args:
        fname (str): filename with mesh specification of doamin in gmsh format
    """
    sp.Popen(['gmsh', '-3', '-v', '3', '-format', 'msh2', fname]).wait()


def convert_mesh(input_mesh, output_mesh):
    """Convert mesh to xml using dolfin-convert.

    Args:
        input_mesh (str): input mesh filename
        output_mesh (str): output mesh filename
    """
    sp.Popen(['dolfin-convert', input_mesh, output_mesh]).wait()
