# REACT over IEEE 802.11
 fabfile.py is the configuration script for fabric
 react.py is the react module which must be run on each node. we need to add a function on fabfile.py to perform a global configuration on nodes
 node_info.txt a csv-like configuration file with topology description
 ieee_stats.sh is a dummy bash script that measure node tx/rx statistics

#setup network
fab -u fabrizio network:freq=5180
#run REACT 
fab -u $(whoami) run_react:bw_req=6000,enable_react='YES'
#run IPERF TEST
fab -u $(whoami) run_trial:prova,'YES'
