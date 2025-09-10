import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

MESH_DENSITY = 0.01

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

# Make the data
x1 = np.arange(-1, 1, MESH_DENSITY)
x2 = np.arange(-1, 1, MESH_DENSITY)
X1, X2 = np.meshgrid(x1, x2)
H = X1 + X2
Y = np.maximum(0, H)
Z = H * 0

ax.plot_surface(
    X1,
    X2,
    Y,
    facecolors=cm.viridis(Y),
    label="y",
    alpha=0.8,
)

# In this example, data where x < 0 or z > 0.5 is clipped
ax.set(
    xlim=(-1, 1),
    ylim=(-1, 1),
    zlim=(0, 2),
    xlabel="x1",
    ylabel="x2",
    zlabel="y",
    xticks=[-1, 0, 1],
    yticks=[-1, 0, 1],
    zticks=[],
)
# ax.legend()

plt.show()
plt.savefig("source/images/plot1.png")
