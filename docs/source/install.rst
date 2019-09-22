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
* `Fenics <https://fenicsproject.org/>`_
  version 2019.1.0 or above recommended
* `pythonocc <https://https://github.com/tpaviot/pythonocc>`_
  version 0.18.2 or above recommended

You must ensure that these are installed prior to module installation.
Recommended approach is to use ``conda`` when able. You can download miniconda
`here <https://docs.conda.io/en/latest/miniconda.html>`_. Create environment
and install available compiled dependencies::

    conda create -n foamgen python pip
    conda activate foamgen
    conda install -c conda-forge cmake gsl fenics
    conda install -c tpaviot -c conda-forge -c dlr-sc -c oce -c pythonocc pythonocc-core=0.18.2 wxPython

Other dependencies are not packaged very well. However, on Ubuntu 18.04, they
can be installed using `install_dependencies.sh
<https://github.com/japaf/foamgen/blob/master/install_dependencies.sh>`_
script::

    sudo ./install_dependencies.sh

Other operating systems and Linux distributions are not tested.

Package
-------

Install using ``pip`` as::

    pip install .

It compiles the package and installs the ``foamgen`` package and executable. If
this fails on cmake compilation, you can check the :ref:`Developer
Installation` for possible solution.
