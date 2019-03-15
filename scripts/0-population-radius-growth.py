import sys, os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from runner import Run, Repeater

L = 2000
R = 20
r = Repeater(length=L, repeat=R)
out = r.go()


fig = plt.figure(1)
ded = 0
fin = np.zeros(R)
maxx = np.zeros(R)
radfin = np.zeros(R)
radstd = np.zeros(R)
ax1 = plt.subplot(221)
ax2 = plt.subplot(222)
ax3 = plt.subplot(223)
ax4 = plt.subplot(224)
for i in range(len(out)):
    plt.sca(ax1)
    plt.plot(out[i].frame, out[i].populus)
    plt.sca(ax2)
    plt.plot(out[i].frame, out[i].radius)

    fin[i] = out[i].populus.iloc[-1]
    maxx[i] = out[i].populus.max()

    radfin[i] = out[i].radius.iloc[-1]
    radstd[i] = out[i].radius.std()

plt.sca(ax3)
plt.scatter(fin, maxx)
plt.xlabel('Final Length')
plt.ylabel('Maximum Length')
plt.sca(ax4)
plt.scatter(radfin, radstd)
plt.xlabel('Final Radius')
plt.ylabel('Radius STD')

plt.sca(ax1)
plt.xlabel('Frame')
plt.ylabel('Population')
plt.title('Population and Radius Growth (POP0 REMOVED:{})'.format(ded))
plt.sca(ax2)
plt.xlabel('Frame')
plt.ylabel('Radius')
plt.show()
