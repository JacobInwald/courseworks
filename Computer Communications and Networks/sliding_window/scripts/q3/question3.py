#!/bin/python3
import os

for i in [1,2,4,8,16,32,64,128,256]:
    print('Testing', i)
    os.system(f'./question3.sh {i}')

