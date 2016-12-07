#! /usr/bin/python

from scapy.all import *
import getopt, sys
import time
import json
import netifaces
import re
import signal

import string, random
import glob

neigh_list = {};
ieee80211_stats={}
ieee80211_stats_={}
pkt_stats={}
C=1
CLAIM_CAPACITY=0.8 # TEST 3,4,bis,5wrong, CLAIM=0.8 TEST1,2 CLAIM_CAPACITY=1 TEST6 CLAIM_CAPACITY=1
mon_iface="mon0"
t_tx=float(time.time())
debug=False
react_count=0

cw_=1023
cw=cw_
data_count_=0
rts_count_=0
starttime=time.time()


MAX_THR=5140 #kbps
rate=0; #APP RATE

"""
REACT INIT
"""
def init(iface):
	global my_mac;
	my_mac=str(netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr'])
	setCW(iface,1,2,15,1023,0)
	init_pkt={};
	init_pkt['t']=0
	init_pkt['offer'] = C
	init_pkt['claim'] = 0
	init_pkt['w'] = 0

	neigh_list[my_mac]=init_pkt


"""
get PHY name for current device
"""
def getPHY(iface="wlan0"):
	devs_info = subprocess.Popen(["iw","dev"], stdout=subprocess.PIPE).communicate()[0]
	pp=str.split(str(devs_info),'\n')
	iii=[x for x in pp if '\t\t' not in x]	
	#phy = subprocess.Popen(["ls", "/sys/kernel/debug/ieee80211/"], stdout=subprocess.PIPE).communicate()[0]
	phy_list={}
	val=[]
	key=''
	for d in iii:
		if '#' in d:
			key=d;
		if iface in d:
			break
			
	phy=key.replace("#","")
	phy="phy0"
	return phy

"""
get iee80211 debugfs packet informations
current format of iee80211_stats:
{'failed_count': 0, 'dot11FCSErrorCount': 3, 'dot11RTSSuccessCount': 0, 'dot11TransmittedFrameCount': 1, 'dot11ACKFailureCount': 0, 'retry_count': 0, 'multiple_retry_count': 0, 'received_fragment_count': 30, 'frame_duplicate_count': 0, 'transmitted_fragment_count': 1, 'multicast_dot11TransmittedFrameCount': 1, 'multicast_received_frame_count': 20, 'dot11RTSFailureCount': 0}
"""
def get_ieee80211_stats(iface,sleeptime):
	global pkt_stats
	phy=getPHY(iface);
	#while True:
	out = subprocess.Popen(["bash","/tmp/ieee_stats.sh",phy,"{}".format(sleeptime)], stdout=subprocess.PIPE).communicate()[0]
	out=out.replace("'", "\"")
	ieee80211_stats_diff=json.loads(str(out))
		#pkt_stats=ieee80211_stats_diff
	return ieee80211_stats_diff

"""
Compute txtime theoretical value for given:
% Input vars:
%   v80211  : '11b', '11g', '11a' or '11p'
%   bitrate : 1,2,5.5,11,6,9,12,18,24,36,48,54
%   bw      : 20,10,5
%   pkt_size: value in byte
% NOTE: pkt_size means  MAC_H + LLC_H  + PAYLOAD + MAC_FCS
"""
def txtime_theor(v80211,bitrate,bw,pkt_size):
    Tpre=16*20/bw;
    Tsig=4*20/bw;
    Tsym=4*20/bw;
    l_ack=14;
    l_rts=20;
    tx_time_theor=0
    if v80211 == '11b':
            CWmin=15;
            tslot=20;
            SIFS=10;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;         
            t_ack=192+l_ack*28/bitrate+1;
            t_rts=192+l_rts*28/bitrate+1;
            tx_time_theor=192+(pkt_size+28)*8/bitrate+1;
            rate=bitrate;
            
            
    elif v80211 == '11g':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=9;
            SIFS=16;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;        
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/rate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/rate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate); 
            

    elif v80211 == '11a':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=9;
            SIFS=16;
            AIFS=3;
            DIFS=AIFS*tslot+SIFS;
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/bitrate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/bitrate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate);
            
    elif v80211 == '11p':
            rate=bitrate*bw/20;
            CWmin=15;
            tslot=13;
            SIFS=32;
            AIFS=2;
            DIFS=AIFS*tslot+SIFS;
            t_ack=Tpre + Tsig+math.ceil(l_ack*8/bitrate);
            t_rts=Tpre + Tsig+math.ceil(l_rts*8/bitrate);
            tx_time_theor= Tpre + Tsig + math.ceil(Tsym/2+(22+8*(pkt_size))/rate);

    return [tslot, tx_time_theor, t_rts, t_ack] 
	
def update_cw(iface,i_time,enable_react,sleep_time,data_path):

	while True:
		if 1:
			update_cw_decision(iface,enable_react,sleep_time,data_path);
		time.sleep(sleep_time - ((time.time() - starttime) % sleep_time))

"""
Set CW
"""

def setCW(iface,qumId,aifs,cwmin,cwmax,burst):

#       echo "0 1 1 3 0" > /sys/kernel/debug/ieee80211/phy0/ath9k/txq_params
#
#       Proper sequence is : "qumId aifs cwmin cwmax burst"

	phy=getPHY(iface);	
	
	f_name='/sys/kernel/debug/ieee80211/{}/ath9k/txq_params'.format(phy);
	txq_params_msg='{} {} {} {} {}'.format(qumId,aifs,cwmin,cwmax,burst)
	f_cw = open(f_name, 'w')
	f_cw.write(txq_params_msg)	

"""
update CW decision based on ieee80211 stats values and virtual channel freezing estimation
"""
def update_cw_decision(iface,enable_react,sleep_time,data_path):
	#get stats
	global my_mac
	global cw
	global cw_
	global data_count_
	global rts_count_
	CWMIN=15
	CWMAX=2047
	pkt_stats=get_ieee80211_stats(iface,sleep_time)
	pkt_size=1534
	if pkt_stats:
		#if rts_count_ == 0 and data_count_ == 0:
		#	data_count = pkt_stats['dot11RTSSuccessCount'] - data_count_
		#	rts_count = pkt_stats['dot11RTSSuccessCount'] + pkt_stats['dot11RTSFailureCount'] - rts_count_
		#	data_count_=pkt_stats['dot11RTSSuccessCount']
		#	rts_count_=pkt_stats['dot11RTSSuccessCount'] + pkt_stats['dot11RTSFailureCount']
		#	return
		data_count = pkt_stats['dot11RTSSuccessCount'] - data_count_
		rts_count = pkt_stats['dot11RTSSuccessCount'] + pkt_stats['dot11RTSFailureCount'] - rts_count_
		data_count_=pkt_stats['dot11RTSSuccessCount']
		rts_count_=pkt_stats['dot11RTSSuccessCount'] + pkt_stats['dot11RTSFailureCount']
		tx_goal=0
		I=0
		dd = sleep_time;
                gross_rate = float(CLAIM_CAPACITY)*float(neigh_list[my_mac]['claim']);
		
		[tslot, tx_time_theor, t_rts, t_ack]= txtime_theor('11a',6,20,pkt_size)
#                busytx2 =  0.002198*float(data_count) + 0.000081*float(rts_count); #how much time the station spent in tx state during the last observation internval
                busytx2 =  0.002071*float(data_count) + 0.000046*float(rts_count); #how much time the station spent in tx state during the last observation internval
		SIFS=16 #usec
		tslot=9e-6 #usec
                #freeze2 = dd - busytx2 - cw_/float(2)*tslot*rts_count - 2*SIFS*1e-6; #how long the backoff has been frozen;
                freeze2 = float(dd) - float(busytx2) - cw_/float(2)*float(tslot)*rts_count; #how long the backoff has been frozen;
		if rts_count > 0:
			avg_tx = float(busytx2)/float(rts_count); #average transmission time in a transmittion cycle
			psucc = float(data_count)/float(rts_count);
		else:
			avg_tx=0
			psucc=0

		if avg_tx > 0:
			tx_goal = float(dd*gross_rate)/float(avg_tx);
		else:
			tx_goal = 0

                freeze_predict = float(freeze2)/float(dd-busytx2)*float(dd-dd*float(gross_rate))  ;


		if tx_goal > 0:
			cw = 2/float(0.000009) * (dd-tx_goal*avg_tx-freeze_predict)/float(tx_goal);


		if cw < CWMIN: 
			cw_=CWMIN
		elif cw > CWMAX:
			cw_=CWMAX
		else:
			# TEST1
			#cw_=cw

 
			# TEST2	CLAIM_CAPACITY = 1; TEST3 CLAIM_CAPACITY = 0.8		
			#cw_=cw 
			#cw_= pow(2, math.ceil(math.log(cw_)/math.log(2)))-1;
			
			#TEST 4 CLAIM_CAPACITY = 0.8 #GOOD
			cw_=cw 
			cw_= pow(2, round(math.log(cw_)/math.log(2)))-1;
			
			#TEST 5 CLAIM_CAPACITY = 1 #BAD!

			#cw_=cw 
			#cw_= pow(2, round(math.log(cw_)/math.log(2)))-1;
			#cw_ = (alpha * cw_ + (1-alpha) * cw );
		
		# ENFORCE CW
		qumId=1 #BE
		aifs=2
		cwmin=int(cw_);
		cwmax=int(cw_);
		burst=0
		if enable_react:
			setCW(iface,qumId,aifs,cwmin,cwmax,burst);
               	thr=(data_count)*1470*8/float(dd*1e6); 
		if debug:
			print "t=%.4f,dd=%.4f data_count=%.4f rts_count=%.4f busytx2=%.4f(%.4f) gross_rate=%.4f,avg_tx=%.4f freeze2=%.4f freeze_predict=%.4f tx_goal=%.4f I=%.4f cw=%.4f cw_=%.4f psucc=%.4f thr=%.4f" % (time.time(),dd,data_count,rts_count,busytx2,busytx2/float(dd),gross_rate,avg_tx,freeze2,freeze_predict,tx_goal,I,cw,cw_,psucc,thr)
		out_val="%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f" % (time.time(),dd,data_count,rts_count,busytx2,gross_rate,avg_tx,freeze2,freeze_predict,tx_goal,I,cw,cw_,psucc,thr)
		
		my_ip=str(netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'])
		out_file="{}/{}.csv".format(data_path,my_ip);
		with open(out_file, "a") as myfile:
			myfile.write(out_val+"\n")
		

def update_offer():
	done = False;
	A = C;
	global my_mac
	D = [key for key,val in neigh_list.items()]
	Dstar=[];	
	while done == False:
		Ddiff=list(set(D)-set(Dstar))
		if set(D) == set(Dstar):
			done = True
			neigh_list[my_mac]['offer'] = A + max([val['claim'] for key,val in neigh_list.items()]) 
		else:
			done = True
			neigh_list[my_mac]['offer'] = A / float(len(Ddiff)) 
			for b in Ddiff:
				if neigh_list[b]['claim'] < neigh_list[my_mac]['offer']:
					Dstar.append(b)
					A -= neigh_list[b]['claim']
					done = False	
def update_claim():
	off_w=[val['offer'] for key,val in neigh_list.items()]
	off_w.append(neigh_list[my_mac]['w'])
	neigh_list[my_mac]['claim']=min(off_w)

def sniffer_REACT(iface,i_time):
	call_timeout=i_time
	call_count=16000
	while True:
		pktlist = scapy.all.sniff(iface=mon_iface, timeout=call_timeout, count=call_count,store=1)
		for pkt in pktlist:
			try:
				rx_mac=str(pkt.addr2)
				if rx_mac == my_mac:
					pass
				else:
					payload=bytes(pkt[2])
					if 'claim' in str(payload):
						payload='{'+re.search(r'\{(.*)\}', str(payload) ).group(1)+'}'
						curr_pkt=json.loads(payload)
						neigh_list[str(rx_mac)]=curr_pkt;
						curr_pkt['t'] = float(time.time())
						update_offer();
						update_claim();
			except (Exception) as err:
				if debug:
					print ( "exception", err)           
				pass






def send_ctrl_msg(iface,json_data):
        a=RadioTap()/Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=my_mac, addr3="ff:ff:ff:ff:ff:ff")/json_data
        sendp(a, iface=mon_iface,verbose=0)

def send_REACT_msg(iface,i_time,iperf_rate,enable_react):
	#TX
	global my_mac
	while True:
    
		rate = min((long)( C ),( (iperf_rate*C)/float(MAX_THR)) );
		neigh_list[my_mac]['w']=rate

		try:
			pkt_to_send={};

			neigh_list[my_mac]['t']=float(time.time())
			pkt_to_send['t']=neigh_list[my_mac]['t']
			pkt_to_send['claim']=neigh_list[my_mac]['claim']
			pkt_to_send['offer']=neigh_list[my_mac]['offer']
			#pkt_to_send['w']=neigh_list[my_mac]['w']
			json_data = json.dumps(pkt_to_send)
			
			#check dead nodes
			timeout = 120
			
			for key,val in neigh_list.items():
				if float(time.time())-val['t'] > timeout:
					neigh_list.pop(key)
			update_offer()
			update_claim()
			# REACT variables updated, transmit!
			send_ctrl_msg(iface,json_data)

		except Exception, err:
			if debug:
				print Exception, err           
			pass

		time.sleep(i_time/10 - ((time.time() - starttime) % i_time/10))

def usage(in_opt,ext_in_opt):
	print("input error: here optionlist: \n{0} --> {1}\n".format(in_opt,str(ext_in_opt)))

def main():
	ext_in_opt=["help", "iface=","tdelay=", "iperf_rate=", "enable_react=", "--output_path"];
	in_opt="hi:t:r:eo:"	
	try:
	    opts, args = getopt.getopt(sys.argv[1:], in_opt, ext_in_opt)
	except getopt.GetoptError as err:
	    # print help information and exit:
	    print str(err)  # will print something like "option -a not recognized"
	    usage(in_opt,ext_in_opt)
	    sys.exit(2)
	i_time=0;
	iface='wlan0';
	iperf_rate=0;
	enable_react=False
	data_path=""

	script_source='\n \
	#! /bin/bash \n \
	#phy_iface="phy0" \n \
	phy_iface="$1" \n \
	sleeptime="$2" \n \
	labels=$(ls /sys/kernel/debug/ieee80211/${phy_iface}/statistics/) \n \
	arr_label=($labels) \n \
	#sleeptime=2 \n \
	line="" \n \
	stats=$(cat /sys/kernel/debug/ieee80211/${phy_iface}/statistics/*) \n \
	arr_stats_start=($stats); \n \
	#sleep $sleeptime \n \
	#stats=$(cat /sys/kernel/debug/ieee80211/${phy_iface}/statistics/*) \n \
	#arr_stats_stop=($stats); \n \
	printf "{" \n \
	for ((i=0;i<${#arr_label[@]} ;i++)) { \n \
	#diff=$(( ${arr_stats_stop[$i]} - ${arr_stats_start[$i]} )); \n \
	diff=${arr_stats_start[$i]} \n \
	if [ $i -eq $(( ${#arr_label[@]} - 1 )) ]; then \n \
		printf "\'%s\' : %s " "${arr_label[$i]}"  "$diff" \n \
	else \n \
		printf "\'%s\' : %s, " "${arr_label[$i]}" "$diff" \n \
	fi \n \
	} \n \
	printf "}" \n \
	ack_fail=$(( ${arr_stats_stop[0]} - ${arr_stats_start[0]} )) \n \
	tx_completed=$(( ${arr_stats_stop[12]} - ${arr_stats_start[12]} )) \n \
	rts_failed=$(( ${arr_stats_stop[2]} - ${arr_stats_start[2]} )) \n \
	rts_success=$(( ${arr_stats_stop[3]} - ${arr_stats_start[3]} )) \n \
	'

	for o, a in opts:
	    if o in ("-i", "--iface"):
		iface = a
	    if o  in ("-t", "--tdelay"):
	       i_time = float(a)
	    if o  in ("-r", "--iperf_rate"):
	       iperf_rate = float(a)
	    if o  in ("-e", "--enable_react"):
	       enable_react=True
	    if o  in ("-o", "--output_path"):
		data_path=str(a)
	    elif o in ("-h", "--help"):
		usage()
		sys.exit()
	#INIT REACT INFO
	f_name='/tmp/ieee_stats.sh';
        ff = open(f_name, 'w')
        ff.write(script_source)
	ff.close()

	my_ip=str(netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'])
	if (not os.path.exists(data_path)):
		print "{} does not exists, please create it".format(data_path)
		return
	out_file="{}/{}.csv".format(data_path,my_ip);
	with open(out_file, "w") as myfile:
		myfile.write("")
		myfile.close()



	init(iface);
	try:

		#Thread transmitter
		thread.start_new_thread( send_REACT_msg,(iface,i_time,iperf_rate,enable_react ) )

		#thread receiver
		thread.start_new_thread( sniffer_REACT,(iface,i_time ) )
		# thread update pkt statistics
		#thread.start_new_thread( get_ieee80211_stats,(iface, i_time) )
		#
		thread.start_new_thread(update_cw,(iface,i_time,enable_react,1,data_path))

	except Exception, err:
		print err
		print "Error: unable to start thread"

	while 1:
	   pass
	
		    
	
if __name__ == "__main__":
    main()
