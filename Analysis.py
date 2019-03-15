import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scripts.runner import Run, Repeater

#==================================ISING
L = 4000
R = 50
thermo = 1
r = Repeater(length=L, repeat=R, grow=False, dim=[100, 100],
             updates=1, rules=[[-1,0,0,-1]], init_noise=0.5,
             beta=.6, thermo=thermo)
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
    plt.sca(ax1)
    out[i].e.plot()
    plt.sca(ax2)
    out[i].m.plot()

    C.append(out[i].heat_capacity.max())
    B.append(out[i].beta.max())

plt.sca(ax3)
plt.scatter(B, C)
plt.xlabel('Beta')
plt.ylabel('Heat Capacity')

plt.sca(ax1)
plt.xlabel('Frame')
plt.ylabel('Energy')
plt.title('Energy and polarizaton of Ising Model (DRAD0 REMOVED:{})'.format(ded))
plt.sca(ax2)
plt.xlabel('Frame')
plt.ylabel('Polarization')
plt.show()

