"""create unstructured tetrahedral mesh"""
from __future__ import print_function
import subprocess as sp
from . import geo_tools


def unstructured_mesh(filename, sizing, convert):
    """Create unstructured mesh."""
    geo_tools.prep_mesh_config(filename, sizing)
    mesh_domain(filename + "UMesh.geo")
    if convert:
        convert_mesh(filename + "UMesh.msh", filename + "UMesh.xml")


def mesh_domain(domain):
    """Mesh computational domain using Gmsh."""
    sp.Popen(['gmsh', '-3', '-v', '3', '-format', 'msh2', domain]).wait()


def convert_mesh(input_mesh, output_mesh):
    """Convert mesh to xml using dolfin-convert."""
    sp.Popen(['dolfin-convert', input_mesh, output_mesh]).wait()
