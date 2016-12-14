import json
import matplotlib.pyplot as plt
import numpy as np

host_mac_map={}
with open('host_mac_map.json') as data_file:    
	host_mac_map=json.load(data_file)

host_list=[str(key) for key in sorted(host_mac_map)]
mac_list=[host_mac_map[key] for key in sorted(host_mac_map)]

conn_matrix={}
for curr_mac in mac_list:
	curr_host=[str(key) for key,value in host_mac_map.items() if value == curr_mac]

	with open ("link-{}.json".format(curr_mac)) as ff:
		dd=json.load(ff)
		a={}
		for k, v in sorted(host_mac_map.items()):
			x=[v_dd["rx"]/float(v_dd["N"]) for k_dd,v_dd in dd.items() if  str(v) == k_dd] 
			if x:
				a[k]=x[0]
			else:
				a[k]=0

		keylist = a.keys()
		keylist.sort()
		curr_val = [a[key] for key in keylist]
			
		conn_matrix[curr_host[0]]=curr_val

mm=[conn_matrix[k] for k in sorted(conn_matrix)]


fig, ax = plt.subplots()

im = ax.matshow(mm, cmap=plt.cm.jet)

fig.colorbar(im, ax=ax)
ax.set_xticks(range(len(host_list)))
ax.set_yticks(range(len(host_list)))
ax.set_xticklabels(host_list)
ax.set_yticklabels(host_list)
plt.show()
