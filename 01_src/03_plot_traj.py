#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pylab as pl
import matplotlib.collections as mcoll
import matplotlib.colors as mcolors
import nmmn.plots

def crystal_site(latt,n_atoms):
    N = int(np.around(n_atoms[1]**(1/3)))
    latt_0 = latt/N
    pos_0 = np.array([
        [1/3,2/3,0.0],
        [2/3,1/3,0.0],
        [0.0,0.0,0.5],
        [0.0,0.0,0.0]
    ])
    pos = []
    for i in range(4):
        for x in range(N):
            for y in range(N):
                for z in range(N):
                    pos_tmp = pos_0[i]+np.array([x,y,z])
                    pos.append(pos_tmp)
    pos = np.array(pos).dot(latt_0)
    return pos

def make_segments(x,y):
    points = np.array([x,y]).T.reshape(-1,1,2)
    segments = np.concatenate([points[:-1],points[1:]],axis=1)
    return segments

def add_time_fade_line(ax, x, y, cmap, values, lw=2.2, alpha_ini=0.15, alpha_end=1.0, zorder=1):
    segments = make_segments(x, y)
    norm = mcolors.Normalize(vmin=np.min(values), vmax=np.max(values))
    rgba = cmap(norm(values[:-1]))
    # rgba[:, 3] = np.linspace(alpha_ini, alpha_end, len(segments))
    linewidths = np.linspace(0.6 * lw, lw, len(segments))
    lc = mcoll.LineCollection(segments, colors=rgba, linewidths=linewidths, zorder=zorder)
    ax.add_collection(lc)
    return lc

#-------------------------------------------------------------------
file_name = "tot_traj"

with open('input','r') as f:
    n_atoms = [int(x) for x in f.readline().split()]
    ntot = np.sum(n_atoms)
    latt = []
    for i in range(3):
        latt.append([float(x) for x in f.readline().split()])
    latt = np.array(latt)

N = int(np.around(n_atoms[1]**(1/3)))
print(f'N_expand = {N}')

with open(file_name,'r') as f:
    traj = []
    while True:
        tmp = f.readline()
        if len(tmp) == 0:
            break
        traj.append([float(x) for x in tmp.split()])

T_ini = 2000
T_end = 2100
traj = np.array(traj).reshape([-1,ntot,3])[T_ini:T_end]
print(np.max(traj),np.min(traj))
print(f'Length of traj : {len(traj)}')

N_Li_in_layer = []
N_N_in_layer = []
half = latt[2,2]/4/4
a1 = latt[0]/N
a2 = latt[1]/N
len_s = (a1+a2)[0]
z_start = -half
z_end = half
x_start = -len_s/4*10
x_end   =  len_s/4*10
for i in range(ntot):
    for j in [0,-1]:
        if z_start < traj[j,i,2] and traj[j,i,2] < z_end and i < n_atoms[0] and i not in N_Li_in_layer:
            N_Li_in_layer.append(i)
        if z_start < traj[j,i,2] and traj[j,i,2] < z_end and i >= n_atoms[0] and i not in N_N_in_layer:
            N_N_in_layer.append(i)

hopping_z = []
for i in N_Li_in_layer:
    if np.linalg.norm(traj[-1,i,:2]-traj[0,i,:2]) > half:
        hopping_z.append(i)
print(hopping_z)

def get_delta_crystal():
    pos_crystal = crystal_site(latt,n_atoms)
    avg_traj = np.sum(traj,axis=0)/len(traj)
    idx_zero = np.argmin(np.linalg.norm(avg_traj,axis=-1))
    avg_diff = avg_traj[idx_zero]
    print('shift',avg_diff)
    return [pos_crystal,avg_diff]

[pos_crystal,avg_diff] = get_delta_crystal()
traj -= avg_diff
print(avg_diff)
x_min = np.min(traj[:,:,0]); x_max = np.max(traj[:,:,0])
y_min = np.min(traj[:,:,1]); y_max = np.max(traj[:,:,1])
z_min = np.min(traj[:,:,2]); z_max = np.max(traj[:,:,2])
xyz_max = np.max([abs(x_min),abs(x_max),abs(y_min),abs(y_max),abs(z_min),abs(z_max)])

# lattice line for ploting lattice
line_latt_1 = np.array([np.array([0.0,0.0]),latt[0,:2],latt[0,:2]+latt[1,:2],latt[1,:2],np.array([0.0,0.0])])
idx = [0,2]
line_latt_2 = np.array([np.array([0.0,0.0]),latt[0,idx]+latt[1,idx],latt[0,idx]+latt[1,idx]+latt[2,idx],latt[2,idx],np.array([0.0,0.0])])
idx = [2,1]
line_latt_3 = np.array([latt[0,idx],latt[1,idx],latt[1,idx]+latt[2,idx],latt[2,idx]+latt[0,idx],latt[0,idx]])


def plot_figure():
    colors = np.linspace(0,1,len(traj))
    fig, ax = plt.subplots(figsize=(2,2))
    parula=nmmn.plots.parulacmap() 
    # for n in range(n_atoms[0]):
    for n in N_Li_in_layer:
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                xy = np.matmul([x,y,0],latt)
                ax.plot(traj[:,n,0]+xy[0],traj[:,n,1]+xy[1],color='0.7',linewidth=0.5,zorder=1)
            
    # for x in [-2,-1,0,1]:
        # for y in [-2,-1,0,1]:
            # xy = np.matmul([x,y,0],latt)
            # ax.scatter(pos_crystal[:int(n_atoms[0]/3*2),0]+xy[0],pos_crystal[:int(n_atoms[0]/3*2),1]+xy[1],linewidth=1,s=100,facecolor='none',edgecolor='k',zorder=10)
    hopping_order= [200,10,100,10,10,10]
    for (i,n)in enumerate(hopping_z):
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                xy = np.matmul([x,y,0],latt)
                x_line = traj[:,n,0] + xy[0]
                y_line = traj[:,n,1] + xy[1]
                lc = add_time_fade_line(
                    ax, x_line, y_line, parula, colors,
                    lw=1.2, alpha_ini=0.0, alpha_end=1.0,
                    zorder=hopping_order[i]
                )
    
    # colorbar --------------------------------
    # cbar = plt.colorbar(lc,ticks=[0,1])
    # cbar.ax.set_yticklabels(['',''])
    # cbar.ax.set_ylabel('Time (ps)',labelpad=-10)
    # ----------------------------------------- 
    a1 = latt[0]/N
    a2 = latt[1]/N
    len_s = (a1+a2)[0]
    print(len_s)
    x_min = -2.0*len_s
    y_min = 1.0*len_s
    xy_len = len_s*4
    print(xy_len)
    bound_x = [x_min,x_min+xy_len]
    bound_y = [y_min,y_min+xy_len]
    x_mean = np.mean(bound_x)
    y_mean = np.mean(bound_y)
    print([x_mean-6,x_mean+6])
    plt.xlim([x_mean-6,x_mean+6])
    plt.ylim([y_mean-6,y_mean+6])
    plt.xticks([])
    plt.yticks([])
    
    for i in N_N_in_layer:
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                xy = np.matmul([x,y,0],latt)
                ax.plot(traj[:,i,0]+xy[0],traj[:,i,1]+xy[1],linewidth=0.5,color='k',zorder=4)

    ax.tick_params(direction='in')
    ax.set_aspect('equal')

    plt.savefig(f'traj_tmp.png',bbox_inches='tight',dpi=600)
plot_figure()
