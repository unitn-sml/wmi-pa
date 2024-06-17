from time import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from wmibench.fairsquare.fairsquare_pysmt import convert

from wmipa import WMI
from wmipa.integration.volesti_integrator import VolestiIntegrator

FONTSIZE = 16

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
    'axes.labelsize': FONTSIZE,
    'font.size': FONTSIZE,
    'legend.fontsize': FONTSIZE,
    'xtick.labelsize': FONTSIZE,
    'ytick.labelsize': FONTSIZE,
})

epsilon = 0.1
repeat = 5
nsamples = 100000
error = 0.001

avgs = []
stds = []
cases = ['unfair', 'fair']
for case in cases:
    prog = convert(f'toy_{case}.fr')

    volesti = VolestiIntegrator(error=error, N=nsamples)
    wmi = WMI(prog.support, prog.weight, integrator=volesti)
    M, MH, nMH = prog.queries

    aggr = []
    taggr = []
    for _ in range(repeat):
        t0 = time()
        p_M, _ = wmi.computeWMI(M, mode=WMI.MODE_SAE4WMI)
        p_MH, _ = wmi.computeWMI(MH, mode=WMI.MODE_SAE4WMI)
        p_nMH, _ = wmi.computeWMI(nMH, mode=WMI.MODE_SAE4WMI)

        p_H_g_M = p_MH / p_M
        p_H_g_nM = p_nMH / (1 - p_M)

        # print("Pr(M):", p_M)
        # print("Pr(H|M):", p_H_g_M)
        # print("Pr(H|~M):", p_H_g_nM)

        ratio = p_H_g_M / p_H_g_nM

        tratio = time() - t0

        print(f"Ratio({case}):", ratio)

        aggr.append(ratio)
        taggr.append(tratio)

        # eps_fairness = (ratio > (1 - epsilon))
        # print("Ratio:", ratio, f"{epsilon}-fairness:", eps_fairness,'\n')

    print(f"Avg. execution time: {np.average(taggr)}")
    avgs.append(np.average(aggr))
    stds.append(np.std(aggr))

# plotting
ax = plt.gca()
ax.set_ylim([0, 1.0])
colors = [(0, 0, 1, 1), (0, 1, 0, 1)]
plt.bar([1, 2], avgs, yerr=stds, tick_label=cases, linewidth=2, color=(0, 0, 0, 0),
        edgecolor=colors)
ax.hlines(y=(1 - epsilon), xmin=0.5, xmax=2.5, linewidth=2, color='r', linestyles='dashed')
plt.text(0.6, (1 - epsilon) + 1e-2, r'$1- \epsilon$', color='r')
plt.ylabel("Fairness ratio")
plt.savefig('fairsquare.pdf', bbox_inches='tight')
print("created fairsquare.pdf")