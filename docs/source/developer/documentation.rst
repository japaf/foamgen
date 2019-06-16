Building the documentation
==========================

Requirements
------------

To be able to build the documentation, the following libraries are required:

* `Sphinx <http://www.sphinx-doc.org/en/master/>`_
* `sphinxcontrib-bibtex <https://pypi.python.org/pypi/sphinxcontrib-bibtex/>`_
* `sphinx_rtd_theme <https://pypi.python.org/pypi/sphinx_rtd_theme/>`_

Installing all of these extensions
can be easily done using the following command::

    pip install sphinx sphinxcontrib-bibtex sphinx_rtd_theme


Making the build
----------------

To build the documentation, execute::

    cd docs
    make html

This should execute sphinx and the documentation should be generated in the
docs/build directory. To open the documentation::

    open build/html/index.html


Documentation guidelines
------------------------

`Google style <http://google.github.io/styleguide/pyguide.html>`_
is followed in documentation of the source code.
