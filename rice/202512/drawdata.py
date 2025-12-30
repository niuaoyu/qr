# import matplotlib.pyplot as plt
# import numpy as np
# plt.rcParams['font.sans-serif']=['SimHei']
# plt.rcParams['axes.unicode_minus']=False
# data=[100,100.6,101.4,101.8,102.3,102.9,103.5,104.0,104.8,105.5,106.1,106.7,107.2,107.9,108.4,109.2,109.8,110.3,110.9,111.6,113.8,111.9,114.2,112.4,116.8,115.1,118.3,116.7,120.0,118.2,121.7,120.0,123.6,121.9,125.4,123.6,127.1,125.3,128.9,127.0,122.0,117.0,112.0,107.0,102.0,97.0,92.0,87.0,82.0,90.0,85.5,94.5,90.0,99.0,94.5,103.5,99.0,108.0,103.5,112.5,108.0,117.0,112.5,121.5,117.0,126.0,121.5,130.5,126.0,135.0,130.5,139.5,135.0,144.0,139.5,148.5,144.0,153.0]
# fig,ax=plt.subplots(figsize=(10,6),facecolor='white')
# ax.plot(data,color='black',linewidth=2,marker='o',markersize=4,markerfacecolor='white',markeredgecolor='black',markeredgewidth=1)
# ax.set_xlim(0,80)
# ax.set_ylim(80,160)
# ax.set_xlabel('days',fontsize=12)
# ax.set_ylabel('price',fontsize=12)
# ax.set_title('randomData',fontsize=14,pad=12)
# ax.grid(True,linestyle='--',alpha=0.5)
# y_ticks=[100,125,150,175]
# ax.set_yticks(y_ticks)
# ax.set_yticklabels([str(tick) for tick in y_ticks])
# x_ticks=[0,20,40,60,80]
# ax.set_xticks(x_ticks)
# ax.set_xticklabels([str(tick) for tick in x_ticks])
# for spine in ax.spines.values():spine.set_linewidth(1.5)
# plt.tight_layout()
# plt.savefig('random_process_plot.png',dpi=300,facecolor=fig.get_facecolor(),edgecolor='none')
# plt.show()

import matplotlib.pyplot as plt
import numpy as np
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)


def step_walk(data, start, end, mod, lt_threshold,
              inc_rng, dec_rng, special_mod=None, special_rng=None):
    for i in range(start, end):
        if i % mod < lt_threshold:
            data[i] = data[i-1] + np.random.uniform(*inc_rng)
        else:
            data[i] = data[i-1] - np.random.uniform(*dec_rng)
        if special_mod and i % special_mod == 0:
            data[i] += np.random.uniform(*special_rng)

days = np.arange(0, 100)
data = np.zeros(100)
data[0] = 100        
step_walk(data, 1, 50, mod=5, lt_threshold=3,
          inc_rng=(2, 4), dec_rng=(1, 2.5),
          special_mod=8, special_rng=(3, 5))
step_walk(data, 50, 70, mod=6, lt_threshold=4,
          inc_rng=(-2, -3.5), dec_rng=(-1, -2),
          special_mod=7, special_rng=(-4, -6))
step_walk(data, 70, 100, mod=5, lt_threshold=3,
          inc_rng=(2, 4), dec_rng=(1, 2.5),
          special_mod=8, special_rng=(3, 5))




# for i in range(1, 41):
#     wave = np.sin(i/3) * 8
#     trend = 0.4 * i
#     noise = np.random.uniform(-2, 2)
#     data2[i] = 30 + trend + wave + noise
# for i in range(41, 61):
#     wave = np.cos((i-40)/2.5) * 6
#     trend = 16 - 0.5 * (i-40)
#     noise = np.random.uniform(-1.5, 1.5)
#     data2[i] = data2[40] + trend + wave + noise
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(days, data, color='gray', linewidth=2.5, label='Series A', marker='o', markersize=4, alpha=0.8)
ax.set_xlabel('days', fontsize=12, fontweight='bold')
ax.set_ylabel('Value', fontsize=12, fontweight='bold')
ax.set_title('randomData', fontsize=14, fontweight='bold', pad=15)
ax.set_xlim(0, 60)
ax.set_ylim(0, 175)
ax.set_xticks(np.arange(0, 61, 5))
ax.set_yticks([100, 125, 150, 175,200, 225, 250, 275])
plt.tight_layout()
plt.savefig('randomData_wave_trend.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.show()
