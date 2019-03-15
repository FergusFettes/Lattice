import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as cl
# peakfinder, use 'prominence' to control
from scipy.signal import find_peaks

from scripts.runner import Run, Repeater

fig = plt.figure(1)
ax1 = plt.subplot(221)
ax2 = plt.subplot(222)
ax3 = plt.subplot(223)
ax4 = plt.subplot(224)
#==================================ISING
L = 20
R = 30
thermo = 0.8

rules = [[2,3,2,3]]
highest = []
fin = pd.DataFrame()
for i in range(8):
    for j in range(8):
        rules[0][1] = i + 1
        rules[0][0] = j + 1
        r = Repeater(length=L, repeat=R, grow=False, dim=[100, 100],
                    updates=1.0, rules=rules, init_noise=0.5,
                    beta=.80, thermo=thermo, squeeze=True)
        out = r.go()
        out['rule'] = ''.join((str(i) for i in rules[0]))
        fin = fin.append(out)

piv = fin.reset_index()
(piv
    .pivot(index='run', columns='rule', values='e')
    .plot(linewidth=1, linestyle='dashed', ax=ax1))
(piv
    .pivot(index='run', columns='rule', values='m')
    .plot(linewidth=2, linestyle='dashed', ax=ax2))

piv.plot(kind='scatter', x='beta', y='C', ylim=[piv.C.min(), piv.C.max()],
            marker='+', ax=ax3)
piv.C.plot(kind='kde', ax=ax3)

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
