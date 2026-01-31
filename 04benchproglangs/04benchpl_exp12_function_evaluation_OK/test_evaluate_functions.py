#!/usr/bin/env python

import numpy as np
import sys

import time

def evaluate_functions(n):
    """
        Evaluate the trigononmetric functions for n values evenly
        spaced over the interval [-1500.00, 1500.00]
    """
    vector1 = np.linspace(-1500.00, 1500.0, n)
    iterations = 10000
    for i in range(iterations):
        vector2 = np.sin(vector1)
        vector1 = np.arcsin(vector2)
        vector2 = np.cos(vector1)
        vector1 = np.arccos(vector2)
        vector2 = np.tan(vector1)
        vector1 = np.arctan(vector2)
    return vector1, vector2

def main(n):
    evaluate_functions(n)

if __name__ == '__main__':
    n = int(sys.argv[1])
    dti = time.perf_counter()
    main(n)
    print(time.perf_counter() - dti)


