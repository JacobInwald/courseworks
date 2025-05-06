#!/bin/python3

import os
import math

NAME = 'stress_{:d}'
TMP_FILE='../data/' + NAME + '-scene.txt'

def construct_scene(n):
    n = int(math.cbrt(n))
    scene = str(n**3) + '\n'
    mesh_str = "box_tri.mesh	250.0	0   {:2f} {:2f} {:2f} 	0.1 1.0 1.0 1.0\n"
    for x in range(n):
        for y in range(n):
            for z in range(n):
                scene += mesh_str.format(30*x, 30*y, 30*z)

    with open(TMP_FILE.format(n**3), 'w') as file:
        file.write(scene)


def results(n):
    print('scene ' + str(n))
    construct_scene(n)
    os.system(f'./test.sh {NAME.format(int(math.cbrt(n))**3)}')

for i in (100, 1000, 5000, 10000):
    results(i)


