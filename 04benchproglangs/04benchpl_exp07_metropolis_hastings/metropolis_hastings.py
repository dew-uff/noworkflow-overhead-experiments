import numpy as np
import sys

import time



def f(x):
    return np.exp(np.sin(x[0]*5) - x[0]*x[0] - x[1]*x[1])



def markov_chain_function(n):
    x = np.zeros((2))
    p = f(x)
    for i in range(n):
        x2 = x + .01*np.random.randn(x.size)
        p2 = f(x2)
        if (np.random.rand() < (p2/p)):
            x = x2
            p = p2
    return x




def main(n):
    y = markov_chain_function(n)

if __name__ == "__main__":
    N = int(sys.argv[1])
    start = time.perf_counter()
    main(N)
    print(time.perf_counter()-start)
