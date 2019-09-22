Packaging
=========

Install ``twine``::

    pip install twine

Create source distribution (don't create platform wheel, because PyPI accepts
only `manylinux1 wheels <https://www.scivision.dev/easy-upload-to-pypi/>`_::

    python setup.py sdist

Test upload to `TestPyPI <https://test.pypi.org>`_::

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

Test installation::

    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple foamgen

Upload to `PyPI <https://pypi.org/>`_::

    twine upload dist/*
