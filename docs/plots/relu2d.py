import matplotlib.pyplot as plt
import numpy as np

DENSITY = 0.01

fig, ax = plt.subplots()

H = np.arange(-1, 1, DENSITY)
Y = np.maximum(0, H)

ax.plot(H, Y, color="C0", alpha=1.0, linewidth=4.0)
ax.plot(H, np.zeros(H.shape), color="C1", linestyle="--", alpha=0.8, linewidth=2.0)
ax.vlines(0, -1, 1, color="C1", linestyle="--", alpha=0.8, linewidth=2.0)

ax.set(
    xlim=(-1, 1),
    ylim=(-1, 1),
    xlabel="h",
    ylabel="y",
    xticks=[-1, 0, 1],
    yticks=[0, 1],
)

plt.gca().set_aspect("equal")
#plt.show()
plt.savefig("source/images/relu2d.png")
