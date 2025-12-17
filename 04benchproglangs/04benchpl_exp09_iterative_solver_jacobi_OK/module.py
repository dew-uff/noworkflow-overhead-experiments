import numpy as np

def loop_time_step(u):
    """
        Take a time step in the desired numerical solution 
        u found using loops
    """
    n, m = u.shape

    error = 0.0
    for i in range(1, n-1):
        for j in range(1, m-1):
            temp = u[i, j]
            u[i, j] = (
                       (u[i-1, j] + u[i+1, j] + u[i, j-1] + u[i, j+1])*4.0 +
                       u[i-1, j-1] + u[i-1, j+1] + u[i+1, j-1] +
                       u[i+1, j+1]
            )/20.0

            difference = u[i, j] - temp
            error += difference*difference

    return u, np.sqrt(error)


#---------------------------
# Function: vector_time_step
#---------------------------
def vector_time_step(u):
    """
        Take a time step in the desired numerical solution v 
        found using vectorization
    """
    u_old = u.copy()
    u[1:-1, 1:-1] = (
                     (u[0:-2, 1:-1] + u[2:, 1:-1] + u[1:-1, 0:-2] +
                      u[1:-1, 2:])*4.0 +
                     u[0:-2, 0:-2] + u[0:-2, 2:] + u[2:, 0:-2] + u[2:, 2:]
    )/20.0

    return u, np.linalg.norm(u-u_old)
