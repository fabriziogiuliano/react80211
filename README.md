# REACT over IEEE 802.11

REACT over IEEE802.11 (aka REACT80211) is a proposed solution for mitigating the performance impairments of CSMA/CA protocols in multi-hop topologies based on the dynamic adaptation of the contention process experienced by nodes in a wireless network. A distributed protocol is used to negotiate the channel airtime for a node as a function of the traffic requirements of its neighbourhood, taking into account bandwidth reserved for the control operations. A mechanism is provided for a node to tune its contention window depending on its allocated airtime. Different from previous schemes, a node's contention window is fixed in size unless the traffic requirements of its neighbourhood change. The scheme is implemented on legacy commercial 802.11 devices supporting ath9k driver.

 - fabfile.py is the configuration script for fabric
 - react.py is the react module which must be run on each node. we need to add a function on fabfile.py to perform a global configuration on nodes
 - node_info.txt a csv-like configuration file with topology description

# INSTALLATION
    git clone https://github.com/fabriziogiuliano/react80211.git
    cd react80211/backports-wireless
    sh build.sh #first time
    sh build.sh --load-module #if build succesfully
    cd ../

# setup network
    fab -u fabrizio network:freq=5180
# run REACT
    mkdir data #first time
    fab -u $(whoami) run_react:bw_req=6000,enable_react='YES'
# run IPERF TEST
    fab -u $(whoami) run_trial:'mytest','YES'
logs are collected inside data/ directory
#   stop test
    fab -u $(whoami) stop_react stop_iperf

# IP.csv log structure
    time.time(),dd,data_count,rts_count,busytx2,gross_rate,avg_tx,freeze2,freeze_predict,tx_goal,I,cw,cw_,psucc,thr

    1481127059.3170,1.0000,44.0000,55.0000,0.0937,0.2667,0.0017,0.8749,0.7079,156.6048,0.0000,36.0885,31.0000,0.8000,0.5174
    1481127060.1606,1.0000,46.0000,48.0000,0.0975,0.2667,0.0020,0.8958,0.7279,131.3171,0.0000,9.2071,15.0000,0.9583,0.5410
    1481127061.2382,1.0000,155.0000,162.0000,0.3285,0.2667,0.0020,0.6606,0.7214,131.5241,0.0000,20.1757,15.0000,0.9568,1.8228
    1481127062.1654,1.0000,308.0000,323.0000,0.6527,0.2667,0.0020,0.3255,0.6873,131.9594,0.0000,77.5323,63.0000,0.9536,3.6221
    1481127063.2013,1.0000,187.0000,234.0000,0.3980,0.2667,0.0017,0.5356,0.6525,156.7678,0.0000,114.5603,127.0000,0.7991,2.1991
    1481127064.2528,1.0000,75.0000,99.0000,0.1599,0.2667,0.0016,0.7835,0.6839,165.1249,0.0000,66.4639,63.0000,0.7576,0.8820

