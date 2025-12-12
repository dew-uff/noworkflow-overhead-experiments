import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'speedupy'))
import numpy as np
import time
import copy

def loop_time_step(u, func_globals=None):
    """
        Take a time step in the desired numerical solution 
        u found using loops
    """
    aux = copy.deepcopy(u)
    (n, m) = aux.shape
    error = 0.0
    for i in range(1, n - 1):
        for j in range(1, m - 1):
            temp = aux[i, j]
            aux[i, j] = ((aux[i - 1, j] + aux[i + 1, j] + aux[i, j - 1] + aux[i, j + 1]) * 4.0 + aux[i - 1, j - 1] + aux[i - 1, j + 1] + aux[i + 1, j - 1] + aux[i + 1, j + 1]) / 20.0
            difference = aux[i, j] - temp
            error += difference * difference
    return (aux, np.sqrt(error))

def loop_solver(n, func_globals=None):
    """
        Find the desired numerical solution using loops
    """
    j = complex(0, 1)
    pi_c = np.pi
    u = np.zeros((n, n), dtype=float)
    x = np.r_[0.0:pi_c:n * j]
    u[0, :] = np.sin(x)
    u[n - 1, :] = np.sin(x) * np.exp(-pi_c)
    iteration = 0
    error = 2
    while iteration < 1000000 and error > 1e-10:
        (u, error) = loop_time_step(u, func_globals=globals())
        iteration += 1
    return (u, error, iteration)

def vector_time_step(u, func_globals=None):
    """
        Take a time step in the desired numerical solution v 
        found using vectorization
    """
    aux = copy.deepcopy(u)
    u_old = aux.copy()
    aux[1:-1, 1:-1] = ((aux[0:-2, 1:-1] + aux[2:, 1:-1] + aux[1:-1, 0:-2] + aux[1:-1, 2:]) * 4.0 + aux[0:-2, 0:-2] + aux[0:-2, 2:] + aux[2:, 0:-2] + aux[2:, 2:]) / 20.0
    return (aux, np.linalg.norm(aux - u_old))

def vectorized_solver(n, func_globals=None):
    """
        Find the desired numerical solution using vectorization
    """
    j = complex(0, 1)
    pi_c = np.pi
    u = np.zeros((n, n), dtype=float)
    x = np.r_[0.0:pi_c:n * j]
    u[0, :] = np.sin(x)
    u[n - 1, :] = np.sin(x) * np.exp(-pi_c)
    iteration = 0
    error = 2
    while iteration < 1000000 and error > 1e-10:
        (u, error) = vector_time_step(u, func_globals=globals())
        iteration += 1
    return (u, error, iteration)

def main():
    num_points = int(sys.argv[1])
    dti = time.perf_counter()
    (u, error, iteration) = loop_solver(num_points, func_globals=globals())
    (u, error, iteration) = vectorized_solver(num_points, func_globals=globals())
    print(time.perf_counter() - dti)
if __name__ == '__main__':
    main()