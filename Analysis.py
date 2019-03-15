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
for i in range(1,9):
    rules[0][0] = i
    r = Repeater(length=L, repeat=R, grow=False, dim=[100, 100],
                updates=1.0, rules=rules, init_noise=0.5,
                beta=.80, thermo=thermo)
    out = r.go()

    ded=0
    C = np.zeros(R)
    D = np.zeros(R)
    for i in out:
        a = out[i]
        plt.sca(ax1)
        a.e.plot(color='k', linewidth=1, linestyle='dashed')
        plt.sca(ax2)
        a.m.plot(color='k', linewidth=2, linestyle='dashed')

        plt.sca(ax3)
        plt.scatter(a.beta.max(), a.heat_capacity.max(), color='g', marker='+')
        C[i] = a.heat_capacity.max()

        plt.sca(ax4)
        plt.scatter(a.beta.max(), a.m.tail(L//5).mean(), color='g', marker='+')
        D[i] = a.m.tail(L//5).mean()

    derived = pd.DataFrame({'C':C, 'D':D})
    derived.C.plot(ax=ax3, kind='kde')
    derived.D.plot(ax=ax4, kind='kde')

    highest.append(derived.C.max())

print(highest)

plt.sca(ax3)
plt.xlabel('Beta')
plt.ylabel('Heat Capacity')
plt.ylim(0, max(highest))
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
