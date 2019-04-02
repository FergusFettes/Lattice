#!/bin/bash
if [ -z $1 ]
then
	echo "needs arg"
else
 	sudo rm -r build/

	sudo python3 setup$1.py build_ext --inplace

 	sudo rm -r build/
	
	if [ -z $2 ]
	then
		python3 ./../testing/test_$1.py
	fi
fi
