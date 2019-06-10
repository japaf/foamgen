Getting Started with Foamgen
============================

Input philosophy
----------------

The value of each parameter of the foam generation process is determined in the
following way:

#. The tool looks if the the value of the parameter was specified through CLI.
#. If the parameter is not specified, but `YAML <https://yaml.org/>`_ config
   file is specified, it looks for it there.
#. If not found, it takes the hard-coded default value of the parameter.

Using config file
-----------------

The config file can be specified as::

    foamgen -c config_file.yml

Getting help
------------

All parameters and their default values can be viewed using::

    foamgen -h

Basic workflow
--------------

The unstructured mesh workflow with default parameters can be run as::

    foamgen -ptmu

**Note: Structured meshing is currently broken. Use only unstructured meshing
workflow.**
