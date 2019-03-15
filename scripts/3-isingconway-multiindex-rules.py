import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# peakfinder, use 'prominence' to control
from scipy.signal import find_peaks

from scripts.runner import Run, Repeater

fig = plt.figure(1)
ax1 = plt.subplot(221)
ax2 = plt.subplot(222)
ax3 = plt.subplot(223)
ax4 = plt.subplot(224)
#==================================ISING
L = 80
R = 30
thermo = 0.8

rules = [[2,3,2,3]]
highest = []
for i in range(8):
    rules[0][0] = i + 1
    r = Repeater(length=L, repeat=R, grow=False, dim=[100, 100],
                updates=1.0, rules=rules, init_noise=0.5,
                beta=.80, thermo=thermo)
    out = r.go()

    piv = out.reset_index()
    (piv
        .pivot(index='fr', columns='run', values='e')
        .plot(color='k', linewidth=1, linestyle='dashed', ax=ax1))
    m = (piv
        .pivot(index='fr', columns='run', values='m'))
    m.plot(color='k', linewidth=2, linestyle='dashed', ax=ax2)

    const = (out
             .swaplevel()       # swaps runs and frames
             .sort_index()      # sorts by frame
             .loc[0])           # selects first frame (constants are same throughout..)

    const.plot(kind='scatter', x='beta', y='C', ylim=[const.C.min(), const.C.max()],
                color='g', marker='+', ax=ax3)
    const.C.plot(kind='kde', ax=ax3)

plt.sca(ax3)
plt.xlabel('Beta')
plt.ylabel('Heat Capacity')
plt.sca(ax4)
plt.xlabel('Beta')
plt.ylabel('Polarization')

plt.sca(ax1)
plt.xlabel('Frame')
plt.ylabel('Energy')
plt.title('Energy and polarizaton of Ising/Conway. Rules:{}'.format(rules))
plt.sca(ax2)
plt.xlabel('Frame')
plt.ylabel('Polarization')
plt.show()
