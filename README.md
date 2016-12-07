# REACT over IEEE 802.11
 fabfile.py is the configuration script for fabric
 react.py is the react module which must be run on each node. we need to add a function on fabfile.py to perform a global configuration on nodes
 node_info.txt a csv-like configuration file with topology description
 ieee_stats.sh is a dummy bash script that measure node tx/rx statistics

#INSTALLATION

cd backports-wireless

sh build.sh #first time

sh build.sh --load-module #if build succesfully

cd ../

#setup network
fab -u fabrizio network:freq=5180
#run REACT 
mkdir data #first time

fab -u $(whoami) run_react:bw_req=6000,enable_react='YES'
#run IPERF TEST
fab -u $(whoami) run_trial:'mytest','YES'

data directory collects experiment logs
#stop test
fab -u $(whoami) stop_react stop_iperf
