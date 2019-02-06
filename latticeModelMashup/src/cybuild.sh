#!/bin/bash
sudo python3 setup.py build_ext --inplace

sudo mv la*/src/Cf*.so ./Cfuncs.so
sudo mv la*/src/CHif*.so ./CHifuncs.so

sudo rm -r la*/

sudo mv C*.c ./cylib
sudo mv C*.html ./build

python3 tests.py
