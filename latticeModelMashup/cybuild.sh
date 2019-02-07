#!/bin/bash
sudo python3 setup.py build_ext --inplace

sudo mv la*/src/Cf*.so ./src/Cfuncs.so

sudo rm -r la*/

sudo mv src/*.c src/build
sudo mv src/C*.html src/build

sudo rm -r build/

python3 tests.py
