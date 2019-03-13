import numpy as np
import pandas as pd

from Xsimple_runner import Run

REPEAT = 50
LENGTH = 1000

R = Run(LENGTH)
R.main()
temp = pd.DataFrame({
    'population':R.TOT,
    'births':R.CHANGE[:, 0],
    'deaths':R.CHANGE[:, 1],
    'growth':R.CHANGE[:, 0] - R.CHANGE[:, 1],
    'turnover':R.CHANGE.sum(axis=1),
    'radius':R.RG,
    'population_density':R.TOT/R.RG if R.RG.any() else 0,
    'axial_diameter':R.AXES.max(axis=1),
})
assert(temp['growth'].sum()==R.TOT[-1])
