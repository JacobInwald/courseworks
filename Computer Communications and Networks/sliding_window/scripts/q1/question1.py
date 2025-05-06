#!/bin/python3
import os

for i in [5,10,15,20,25,30,40,50,75,100]:
    print('Testing', i)
    os.system(f'./question1.sh {i}')

