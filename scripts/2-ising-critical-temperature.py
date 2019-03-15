import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scripts.runner import Run, Repeater

#==================================ISING
L = 4000
R = 40
thermo = 0.3
r = Repeater(length=L, repeat=R, grow=False, dim=[100, 100],
             updates=1, rules=[[-1,0,0,0]], init_noise=0.5,
             beta=.43, thermo=thermo)
out = r.go()

fig = plt.figure(1)
ax1 = plt.subplot(221)
ax2 = plt.subplot(222)
ax3 = plt.subplot(223)
ax4 = plt.subplot(224)
ded=0
C = []
B = []
for i in out:
    a = out[i]
    plt.sca(ax1)
    a.e.plot()
    plt.sca(ax2)
    a.m.plot()

    plt.sca(ax3)
    plt.scatter(a.beta.max(), a.heat_capacity.max(), color='b', marker='+')

    plt.sca(ax4)
    plt.scatter(a.beta.max(), a.m.tail(L//5).mean(), color='k', marker='+')


plt.sca(ax3)
plt.xlabel('Beta')
plt.ylabel('Heat Capacity')
plt.ylim(0, 1e-4)
plt.sca(ax4)
plt.xlabel('Beta')
plt.ylabel('Polarization')

plt.sca(ax1)
plt.xlabel('Frame')
plt.ylabel('Energy')
plt.title('Energy and polarizaton of Ising Model (DRAD0 REMOVED:{})'.format(ded))
plt.sca(ax2)
plt.xlabel('Frame')
plt.ylabel('Polarization')
plt.show()

