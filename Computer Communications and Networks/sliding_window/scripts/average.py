#!/bin/python3

import sys
import numpy as np

if len(sys.argv) != 2:
    print('Usage: average.py <file>')

fp = sys.argv[1]


data = []
with open(fp, 'r') as f:
    for line in f.readlines():
        data.append(line.strip())

for i, r in enumerate(data):
    data[i] = [float(s) for s in r.split() if s != '']

data = np.array(data)
data = data.transpose()
[print(f'{a.mean():.2f}') for a in data]
