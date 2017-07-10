import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
from matplotlib import animation
import scipy.integrate as integral

make_animation = True

height        = 8.0  # inches
diameter      = 1.0  # inches
mesh_step     = 0.01  # inches ([height,diameter] / mesh_step is integer)
core_diameter = 0.2  # inches (even multiple of mesh_step)

J = int(height / mesh_step)   # number of rows
N = int(diameter / mesh_step) # number of cols


# i know this is ugly
def to_burn(row, col, grid):
    left    = False if col - 1 <= 0            else True
    right   = False if col + 1 >= len(grid[0]) else True
    top     = False if row - 1 <= 0            else True
    bottom  = False if row + 1 >= len(grid)    else True
    top2    = False if row - 2 <= 0            else True
    if left   and grid[row, col-1] == 2:
        return True
    if right  and grid[row, col+1] == 2:
        return True
    if top    and grid[row-1, col] == 2:
        return True
    if bottom and grid[row+1, col] == 2:
        return True
    if top2 and grid[row-2, col] == 2:
        return True
    else:
        return False

rocket = np.zeros((J, N)) # meshgrid: 0 is yellow (fuel)
                          #           1 is white (gas),
                          #           2 is red (burning)  


core_number = int(core_diameter / mesh_step)
core_start = (N - core_number) / 2
cores = range(core_start, core_start + core_number)

rocket[:, cores] = 1.0
rocket[38:42, [cores[0], cores[-1]]] = 2.0

fig = plt.figure()
ax = plt.axes(xlim=(0, diameter), ylim=(0, height))

out = []

out.append(rocket)

t = 1
while 0 in rocket:
    new_rocket = rocket.copy()
    for i in range(0, J):
        for j in range(0, N):
            cell = rocket[i, j]
            if cell == 0:
                if to_burn(i, j, rocket):
                    new_rocket[i, j] = 2
            elif cell == 1:
                pass
            elif cell == 2:
                new_rocket[i,j] = 1

    rocket = new_rocket
    out.append(rocket)

rocket = np.ones((J, N)) * 1.
out.append(rocket)

def animate(i):
    rocket = out[i]
    if i == len(out) - 1:
        cmap = clrs.ListedColormap(['white', 'red'])
    elif i == len(out):
        cmap = clrs.ListedColormap(['white'])
    else:
        cmap = clrs.ListedColormap(['yellow', 'white', 'red'])
    
    plt.clf()
    return plt.pcolor(rocket, cmap=cmap, edgecolors='black')

if make_animation:
    anim = animation.FuncAnimation(fig, animate, frames=len(out))
    anim.save('burn-simulation-%s.mp4' % mesh_step, fps=25)

tseries = np.array(map(lambda rocket: np.count_nonzero(rocket==2.), out))
plt.clf()
plt.cla()
plt.close()
plt.plot(range(len(tseries)), tseries)
plt.xlabel('Time')
plt.ylabel('Burning cells')
tit = '%s by %s in. rocket with %s in. core diameter' % (diameter,
                                                         height,
                                                         core_diameter)
plt.title(tit)
plt.savefig('timeseries-%s.png' % mesh_step)

print 'Integrated thrust: %s' % (integral.trapz(tseries) * mesh_step ** 2)

