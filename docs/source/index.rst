Foamgen: generate foam morphology
=================================

Foamgen is a package that can be used to create spatially three-dimensional
virtual representations of foam morphology with desired foam density, cell size
distribution and strut content.

Here are some features of Foamgen:

* Generation of closed-cell and open-cell morphology
* Input parameters are based on physical aspects that can be experimentally
  determined
* Cells are created using weighted tessellation so that desired size
  distribution is achieved
* Mesh generated foam either using structured equidistant grid or unstructured
  tetrahedral mesh
* Modular - easy to run only parts of the generation process
* Open-source package with MIT license

Structured mesh workflow consists of several steps (for more details see
:cite:`Ferkl2018`):

#. Dense sphere packing
#. Laguerre tessellation
#. Geometric morphology creation
#. Meshing

References
----------
.. bibliography:: library.bib

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   tutorials/index
   developer/index
   about


.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
