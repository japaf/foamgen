Developer Installation
======================

If you intend to commit code, you should fork the repo and clone it using
(don't forget to change the username)::

    git clone git@github.com:japaf/foamgen.git

If you don't intend to commit code, you can clone the repo without forking
using::

    git clone https://github.com/japaf/foamgen.git


Next, install all dependencies as explained in :ref:`Requirements`. Finally,
install package for development using::

    pip install -e .

If the install fails on cmake installation, check the `CMakeLists.txt
<https://github.com/japaf/foamgen/blob/master/CMakeLists.txt>`_. Note that the
installation path of Voro++ library is unfortunately hard-coded, so you may
need to change it.
