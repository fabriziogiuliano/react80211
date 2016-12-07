 fabfile.py is the configuration script for fabric
 react.py is the react module which must be run on each node. we need to add a function on fabfile.py to perform a global configuration on nodes
 node_info.txt a csv-like configuration file with topology description
 ieee_stats.sh is a dummy bash script that measure node tx/rx statistics

#setup network
fab -u fabrizio network:freq=5180
#run REACT 
-i iface -t ctrl-msg-freq -r bw_req

sudo python react.py -i wlan0 -t 0.1 -r 3000
