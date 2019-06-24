Installation
============

Requirements
------------

Foamgen requires following programs and libraries:

* `CMake <http://www.cmake.org>`_ version 2.8.12 or above
* `Python <http://www.python.org/>`_ version 3.5 or above
* `packing-generation <https://github.com/VasiliBaranov/packing-generation.git>`_
  version 1.0.1.28 or above recommended
* `Neper <http://neper.sourceforge.net/index.html>`_
  version 3.4.0 or above recommended
* `Voro++ <http://math.lbl.gov/voro++/about.html>`_
  version 0.4.6 or above recommended
* `binvox <http://www.patrickmin.com/binvox/>`_
  version 1.27 or above recommended
* `GSL <http://www.gnu.org/software/gsl/>`_
  version 2.3 or above recommended

You must ensure that these are installed prior to module installation.

On Ubuntu 18.04, all of these can be installed using `install_dependencies.sh
<https://github.com/japaf/foamgen/blob/master/install_dependencies.sh>`_
script::

    sudo ./install_dependencies.sh

Moreover, `fenics <https://fenicsproject.org/>`_ (or at least
``dolfin-convert``) is necessary for mesh conversion.

Other operating systems and Linux distributions are not tested.

Package
-------

Install using ``pip`` as::

    pip install .

It compiles the package and installs the ``foamgen`` package and executable.
