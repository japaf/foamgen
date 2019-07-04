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

Importing package
-----------------

``foamgen`` can also be imported as a python module. For example, to create
sphere packing, following code can be run::

    import foamgen as fg
    cfg = fg.generation.parse_config_file('basic.yml')
    cfg.pack.active = True
    fg.generation.generate(cfg)

where ``basic.yml`` is a valid configurational file. Such file can be found in
``examples`` directory.
