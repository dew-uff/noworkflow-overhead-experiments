import time
from math import sqrt
from numpy import empty, array
from matplotlib.pylab import imshow, cm, show
from module import in_sponge

def cross_product(v, w):
    v1, v2, v3 = v
    w1, w2, w3 = w
    return (v2*w3 - v3*w2, v3*w1 - v1*w3, v1*w2 - v2*w1)

def length(v):
    "Euclidean length"
    x, y, z = v
    return sqrt(x*x + y*y + z*z)

def plot_slice(normal, point, level, n):
    """Plot a slice through the Menger sponge by
    a plane containing the specified point and having
    the specified normal vector. The view is from
    the direction normal to the given plane."""

    # t is an arbitrary point
    # not parallel to the normal direction.
    nx, ny, nz = normal
    if nx != 0:
        t = (0, 1, 1)
    elif ny != 0:
        t = (1, 0, 1)
    else:
        t = (1, 1, 0)

    # Use cross product to find vector orthogonal to normal
    cross = cross_product(normal, t)
    v = array(cross) / length(cross)

    # Use cross product to find vector orthogonal
    # to both v and the normal vector.
    cross = cross_product(normal, v)
    w = array(cross) / length(cross)

    m = empty( (n, n), dtype=int )
    h = 1.0 / (n - 1)
    k = 2.0*sqrt(3.0)

    for x in range(n):
        for y in range(n):
            pt = point + (h*x - 0.5)*k*v + (h*y - 0.5)*k*w
            m[x, y] = 1 - in_sponge(pt, level)
    imshow(m, cmap=cm.gray)
    show(block=False)

def main():
    # Specify the normal vector of the plane
    # cutting through the cube.
    normal = (1, 1, 0.5)

    # Specify a point on the plane.
    point = (0.5, 0.5, 0.5)

    level = 3
    n = 6500
    plot_slice(normal, point, level, n)
start = time.perf_counter()
main()
print(time.perf_counter() - start)
