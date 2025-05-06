#!/bin/python3

import matplotlib.pyplot as plt
import numpy as np
import os
import sys

gap = 30 

def parse_data(fp):
    data = os.open(fp, os.O_RDONLY)
    _data = []

    for line in os.read(data, os.path.getsize(fp)).splitlines():
        if 'FPS' in line.decode(): 
            _data.append(abs(float(line.split()[1])))

    fps = np.array(_data)
    spf = 1 / fps 

    second = cur_fps = count = 0
    y = []
    for _fps, _spf in zip(fps, spf):
        second += _spf
        cur_fps += _fps
        count += 1
        if count >= gap:
            y.append(cur_fps / count)
            second = 0
            cur_fps = 0
            count = 0

    # Plot the data
    y = np.array(y)
    y = 1000 / y
    x = np.array(range(len(y))) * gap
    if x.size == 0:
        y = np.zeros(100) 
        x = np.array(range(len(y))) * gap
    return x, y

try: 
    x_opt, y_opt = parse_data(sys.argv[1])
    x, y = parse_data(sys.argv[2])
except: 
    print("Usage: python3 fps-visualise.py <file-optimized> <file-unoptimized>")
    exit(1)



plt.rcParams.update({'font.size': 16})
# let us make a simple graph
fig = plt.figure(figsize=(8,6))
ax = plt.subplot(111)

# ax.fill_between(x, y, alpha=0.7)

# change the fill into a blueish color with opacity .3
ax.plot(x, y, c='black', lw=2, label='Base')
ax.plot(x_opt, y_opt, c='red', lw=2, label='Optimized')

xlim = min(max(x_opt), max(x))
ylim = max(max(y_opt) + max(y_opt) * 0.1, max(y) + max(y) * 0.1)

ax.set_xlim(0, xlim)
ax.set_ylim(0, ylim)

# remove tick marks
ax.xaxis.set_tick_params(size=0)
ax.yaxis.set_tick_params(size=0)
# set the basic properties
ax.set_xlabel('Frame Count')
ax.set_ylabel('Frame Generation Time / ms')

ax.set_title(f"Frame Generation Time for {sys.argv[1].split('-')[0].split('/')[1]} scene")
# set the grid on
ax.grid(which='major', linestyle='-.', linewidth='0.5', color='grey')
ax.legend()

sp = sys.argv[3]
plt.savefig(sp)


