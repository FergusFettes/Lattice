#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from latticeModelMashup.src.Cfuncs import *
from latticeModelMashup.src.Pfuncs import *
from cpython cimport array
cimport numpy as np
