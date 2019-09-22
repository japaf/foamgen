#!/bin/bash
apts () {
    sudo apt-get install cmake
}

packinggeneration () {
    cd /tmp
    git clone https://github.com/VasiliBaranov/packing-generation.git
    cd packing-generation/_Release
    make
    sudo cp PackingGeneration.exe /usr/local/bin
    cd /tmp
    rm -rf packing-generation
}

neper () {
    sudo apt-get install libgsl-dev libscotch-dev povray povray-includes \
    libnlopt-dev
    NEPER_VERSION=3.4.0
    echo "Installing NEPER version $NEPER_VERSION"
    cd /tmp
    wget https://github.com/rquey/neper/archive/$NEPER_VERSION.tar.gz
    tar -xf $NEPER_VERSION.tar.gz
    cd neper-$NEPER_VERSION/src
    mkdir build
    cd build
    cmake ..
    make
    sudo make install
    cd /tmp
    rm $NEPER_VERSION.tar.gz
    rm -rf neper-$NEPER_VERSION
}

voroplusplus () {
    VORO_VERSION=0.4.6
    echo "Installing VORO version $VORO_VERSION"
    cd /tmp
    wget http://math.lbl.gov/voro++/download/dir/voro++-$VORO_VERSION.tar.gz
    tar -xf voro++-$VORO_VERSION.tar.gz
    cd voro++-$VORO_VERSION
    make
    sudo make install
    cd /tmp
    rm voro++-$VORO_VERSION.tar.gz
    rm -rf voro++-$VORO_VERSION
}

binvox () {
    wget http://www.patrickmin.com/binvox/linux64/binvox
    chmod ug+x binvox
    sudo mv binvox /usr/local/bin/binvox
}

gsl () {
    # stopped working for me, try to use conda install -c conda-forge gsl
    sudo apt-get install libgsl-dev
}

apts |& tee apts.log
packinggeneration |& tee packinggeneration.log
neper |& tee neper.log
voroplusplus |& tee voroplusplus.log
binvox |& tee binvox.log
gsl |& tee gsl.log
