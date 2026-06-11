#!/usr/bin/env python3

import numpy as np

with open('xdatcar.md3','r') as f:
    f.readline()
    f.readline()
    latt = []
    for i in range(3):
        latt.append([float(x) for x in f.readline().split()])
    latt = np.array(latt)
    at_name = f.readline().split()
    n_atoms = [int(x) for x in f.readline().split()]
    ntot = np.sum(n_atoms)
    pos = []
    while True:
        tmp = f.readline()
        if len(tmp) == 0:
            break
        for i in range(ntot):
            pos.append([float(x) for x in f.readline().split()])

pos = np.array(pos)
for i in range(3):
    pos[pos[:,i]  >  0.5, i] -= 1.0
    pos[pos[:,i] <= -0.5, i] += 1.0
pos_xyz = np.matmul(pos,latt)
pos = pos.reshape([-1,ntot,3])
pos_xyz = pos_xyz.reshape([-1,ntot,3])
with open('xdatcar_shift','w') as f:
    f.write('xdatacr.md3_shift\n')
    f.write('1\n')
    for i in range(3):
        f.write(f'{latt[i,0]:20.6f} {latt[i,1]:20.6f} {latt[i,2]:20.6f}\n')
    f.write('  '.join(at_name)+'\n')
    f.write('  '.join([f'{x:5.0f}' for x in n_atoms])+'\n')
    for i in range(len(pos)):
        f.write(f'Direct configuration={i:5.0f}\n')
        for j in range(ntot):
            f.write(f'{pos[i,j,0]:20.8f} {pos[i,j,1]:20.8f} {pos[i,j,2]:20.8f}\n')