import matplotlib.pyplot as plt
import numpy as np

DENSITY = 0.01
FONTSIZE = 16.0
FGAP = 0.05

fig, ax = plt.subplots()

ax.plot([0, 0], [1, 0], color="C0", alpha=0.8, linewidth=4.0)
ax.plot([1, 0], [0, 0], color="C0", alpha=0.8, linewidth=4.0)

ax.plot([1, 0], [0, 1], color="C1", alpha=0.8, linewidth=4.0)

ax.plot([1, 1], [0, 1], color="C2", alpha=0.8, linewidth=4.0)
ax.plot([0, 1], [0, 1], color="C2", alpha=0.8, linewidth=4.0)

ax.text(1 / 4 - FGAP, 1 / 2 - FGAP, "$\mu_1$", size=FONTSIZE)
ax.text(1 / 2 - FGAP, 1 / 4 - FGAP, "$\mu_2$", size=FONTSIZE)
ax.text(3 / 4 - FGAP, 1 / 2 - FGAP, "$\mu_3$", size=FONTSIZE)

ax.set(
    xlim=(-0.1, 1.1),
    ylim=(-0.1, 1.1),
    xlabel="x",
    ylabel="y",
    xticks=[0, 1],
    yticks=[0, 1],
)

plt.gca().set_aspect("equal")
# fig.tight_layout(rect=[-0.2, -0.2, 1.2, 1.2], pad=0)
# plt.show()

plt.savefig("source/images/example3.png", transparent=True)
