import numpy as np
import pandas as pd

from Xsimple_runner import Run, Repeater

L = 200
R = 100
r = Repeater(length=L, repeat=R)
out = r.go()
stds = []
for i in range(R):
    stds.append(out[i].describe().population[2])
