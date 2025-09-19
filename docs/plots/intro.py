import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

MESH_DENSITY = 1
FONT_SIZE = 8


plt.rcParams.update({'font.size': FONT_SIZE})
fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

x = np.arange(0, 10, MESH_DENSITY)
y = np.arange(0, 10, MESH_DENSITY)
z = np.arange(0, 10, MESH_DENSITY)
X, Y = np.meshgrid(x, y)
Z = np.abs(X * np.sin((X + Y)*17))

norm = plt.Normalize(Z.min(), Z.max())

ax.plot_surface(
    X,
    Y,
    Z,
    facecolors=cm.viridis(norm(Z)),
    alpha=0.6,
)


ax.set(
    xlim=(0, 10),
    ylim=(0, 10),
    zlim=(0, 10),
    xlabel="$x$",
    ylabel="$y$",
    zlabel="$P(x, y)$",
    xticks=[],
    yticks=[],
    zticks=[],
)

plt.savefig("source/images/intro.png", transparent=True, dpi=300)
plt.show()
