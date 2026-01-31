#!/usr/bin/env python

import numpy as np
import sys

import time



##integrand = lambda x: np.exp(x)

def integrand(t):
    return np.exp(t)

def compute_quadrature(n):
    """
      Perform the Gauss-Legendre Quadrature at the prescribed order n
    """
    a = -3.0
    b = 3.0

    # Gauss-Legendre (default interval is [-1, 1])
    x, w = np.polynomial.legendre.leggauss(n)

    # Translate x values from the interval [-1, 1] to [a, b]
    t = 0.5*(x + 1)*(b - a) + a

    return sum(w * integrand(t)) * 0.5*(b - a)


def main(order):
    compute_quadrature(order)


if __name__ == '__main__':

    order = int(sys.argv[1])
    dti = time.perf_counter()
    main(order)
    print(time.perf_counter() - dti)
