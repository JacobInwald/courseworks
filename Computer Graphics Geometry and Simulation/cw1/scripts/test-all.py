#!/bin/python3

import os


fps = []
for fp in os.listdir('../data'):
    name = fp.split('-')[0]
    if name in fps or \
        '.' in name or \
        'scene' not in fp:
        continue
    fps.append(name)

fps = set(fps)

for f in fps:
    print('scene ' + str(f))
    os.system(f'./test.sh {f}')
