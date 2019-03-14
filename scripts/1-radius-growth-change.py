import sys, os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from runner import Run, Repeater

L = 300
R = 50
r = Repeater(length=L, repeat=R)
out = r.go()

fig = plt.figure(1)
t1 = []; t2 = []; t3 = []
ax1 = plt.subplot(221)
ax2 = plt.subplot(223)
ax3 = plt.subplot(222)
ax4 = plt.subplot(224)
ded = 0
for i in out:
    if not out[i].Drad.tail(100).mean(): ded += 1; continue

    t1.append(
        out[i].Drad.tail(100).std()
    )
    t2.append(
        out[i].Drad.tail(100).mean()
    )
    t3.append(
        out[i].iloc[-1].seed
    )

    plt.sca(ax1)
    out[i].radius.plot()
    plt.sca(ax2)
    out[i].Drad.plot()

R = pd.DataFrame({'instance':pd.Series(range(len(t1)))})
R['end_std'] = t1
R['end_mean'] = t2
R['seed'] = t3

plt.sca(ax3)
R.end_mean.hist()
plt.ylabel('Mean (end)')

plt.sca(ax4)
R.end_std.hist()
plt.ylabel('Std (end)')

plt.sca(ax1)
plt.xlabel('Frame')
plt.ylabel('Radius')
plt.title('Radius Growth (DRAD0 REMOVED:{})'.format(ded))
plt.sca(ax2)
plt.xlabel('Frame')
plt.ylabel('Change in Radius')
plt.show()

