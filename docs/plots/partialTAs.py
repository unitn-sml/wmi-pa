import matplotlib.pyplot as plt
import numpy as np

#### TOTAL

fig, ax = plt.subplots()

ax.plot([0, 1], [0, 0], color="black", alpha=1.0, linewidth=4.0)  # bounding box
ax.plot([0, 1], [1, 1], color="black", alpha=1.0, linewidth=4.0)
ax.plot([0, 0], [0, 1], color="black", alpha=1.0, linewidth=4.0)
ax.plot([1, 1], [0, 1], color="black", alpha=1.0, linewidth=4.0)

ax.plot([1 / 4, 1 / 2], [1 / 2, 1 / 4], color="black", alpha=1.0, linewidth=4.0)
ax.plot([0, 3 / 4], [3 / 4, 0], color="black", alpha=0.8, linewidth=4.0, linestyle="--")

ax.plot([3 / 4, 1 / 2], [1 / 2, 1 / 4], color="black", alpha=1.0, linewidth=4.0)
ax.plot([1 / 4, 1], [0, 3 / 4], color="black", alpha=0.8, linewidth=4.0, linestyle="--")

ax.plot([1 / 4, 1 / 2], [1 / 2, 3 / 4], color="black", alpha=1.0, linewidth=4.0)
ax.plot([0, 3 / 4], [1 / 4, 1], color="black", alpha=0.8, linewidth=4.0, linestyle="--")

ax.plot([1 / 2, 3 / 4], [3 / 4, 1 / 2], color="black", alpha=1.0, linewidth=4.0)
ax.plot([1 / 4, 1], [1, 1 / 4], color="black", alpha=0.8, linewidth=4.0, linestyle="--")

ax.fill_between([1 / 4, 1 / 2, 3 / 4], [1 / 2, 1 / 4, 1 / 2], [1 / 2, 3 / 4, 1 / 2])

ax.set(
    xlim=(-0, 1),
    ylim=(-0, 1),
    xlabel="x",
    ylabel="y",
    xticks=[0, 1],
    yticks=[0, 1],
)

plt.gca().set_aspect("equal")
# plt.show()

plt.savefig("source/images/partialTAs1.png", transparent=True)
plt.clf()

#### PARTIAL

fig, ax = plt.subplots()

ax.plot([0, 1], [0, 0], color="black", alpha=1.0, linewidth=4.0)  # bounding box
ax.plot([0, 1], [1, 1], color="black", alpha=1.0, linewidth=4.0)
ax.plot([0, 0], [0, 1], color="black", alpha=1.0, linewidth=4.0)
ax.plot([1, 1], [0, 1], color="black", alpha=1.0, linewidth=4.0)

ax.plot([1 / 4, 1 / 2], [1 / 2, 1 / 4], color="black", alpha=1.0, linewidth=4.0)
ax.plot([0, 3 / 4], [3 / 4, 0], color="black", alpha=0.8, linewidth=4.0, linestyle="--")

ax.plot([3 / 4, 1 / 2], [1 / 2, 1 / 4], color="black", alpha=1.0, linewidth=4.0)
ax.plot(
    [1 / 2, 1], [1 / 4, 3 / 4], color="black", alpha=0.8, linewidth=4.0, linestyle="--"
)

ax.plot([1 / 4, 1 / 2], [1 / 2, 3 / 4], color="black", alpha=1.0, linewidth=4.0)

ax.plot([1 / 2, 3 / 4], [3 / 4, 1 / 2], color="black", alpha=1.0, linewidth=4.0)
ax.plot(
    [1 / 4, 3 / 4], [1, 1 / 2], color="black", alpha=0.8, linewidth=4.0, linestyle="--"
)

ax.fill_between([1 / 4, 1 / 2, 3 / 4], [1 / 2, 1 / 4, 1 / 2], [1 / 2, 3 / 4, 1 / 2])

ax.set(
    xlim=(-0, 1),
    ylim=(-0, 1),
    xlabel="x",
    ylabel="y",
    xticks=[0, 1],
    yticks=[0, 1],
)

plt.gca().set_aspect("equal")
plt.show()

plt.savefig("source/images/partialTAs2.png", transparent=True)
plt.clf()
