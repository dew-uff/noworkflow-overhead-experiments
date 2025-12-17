import sys
import numpy as np
import time
from module import loop_time_step, vector_time_step

#----------------------
# Function: loop_solver
#----------------------

def loop_solver(n):
    """
        Find the desired numerical solution using loops
    """

    j = complex(0, 1)
    pi_c = np.pi

    # Set the initial condition
    u = np.zeros((n, n), dtype=float)

    #       Set the boundary condition
    x = np.r_[0.0:pi_c:n*j]
    u[0, :] = np.sin(x)
    u[n-1, :] = np.sin(x)*np.exp(-pi_c)

    iteration = 0
    error = 2
    while(iteration < 100000 and error > 1e-10):
        (u, error) = loop_time_step(u)
        iteration += 1
    return (u, error, iteration)

#----------------------------
# Function: vectorized_solver
#----------------------------
def vectorized_solver(n):
    """
        Find the desired numerical solution using vectorization
    """
    j = complex(0, 1)
    pi_c = np.pi

    # Set the initial condition
    u = np.zeros((n, n), dtype=float)

    # Set the boundary condition
    x = np.r_[0.0:pi_c:n*j]
    u[0, :] = np.sin(x)
    u[n-1, :] = np.sin(x)*np.exp(-pi_c)

    iteration = 0
    error = 2
    while(iteration < 100000 and error > 1e-10):
        (u, error) = vector_time_step(u)
        iteration += 1
    return (u, error, iteration)


# number of grid points
# def main0(num_points):
    
# def main1(num_points):
    
def main():
    num_points = int(sys.argv[1])
    #print('LOOP')
    dti = time.perf_counter()
    #main0(num_points)
    (u, error, iteration) = loop_solver(num_points)
    # print(time.perf_counter() - dti)
    #print('VECTOR')
    # dti = time.perf_counter()
    #main1(num_points)
    (u, error, iteration) = vectorized_solver(num_points)
    print(time.perf_counter() - dti)

if __name__ == '__main__':
    main()