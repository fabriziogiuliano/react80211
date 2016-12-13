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
import socket

mon_iface="mon0"
debug=False
starttime=time.time()



"""
REACT INIT
"""
def init(iface="wlan0"):
	global my_mac;
	my_mac=str(netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr'])

def sniffer_probes(iface,i_time,data_path):
	call_timeout=i_time
	call_count=100
	rx_count=0
        #my_ip=str(netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'])
        my_mac=str(netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr'])
        out_file="{}/link-{}.json".format(data_path,my_mac);
        #if not os.path.exists(out_file):
        #        open_file_mode="w";
        #else:
        #        open_file_mode="a";

	res_data={}
	res_val={}
	res_data["t"]=float(time.time())
	res_data["rx"]=rx_count;
	res_data["N"]=0
	json_val=""
	if os.path.exists(out_file):
		try:
			with open(out_file) as data_file:    
				res_val=json.load(data_file)
				json_val=json.dumps(res_val)
				print "previous loaded file loaded: {}".format(json_val)
		except (Exception) as err:
			print "file {} does not contain a correcct json format, create empty file".format(out_file)
			json_val=""
			res_val={}
	else:
		print "no previous json logs: create new log"
	while True:
		t_now=time.time();
		pktlist = scapy.all.sniff(iface=mon_iface, timeout=call_timeout, count=call_count,store=1)
		for pkt in pktlist:
		
			try:
				rx_mac=str(pkt.addr2)
				if rx_mac == my_mac:
					pass
				else:
					payload=bytes(pkt[2])
					if 'seq' in str(payload):
						payload='{'+re.search(r'\{(.*)\}', str(payload) ).group(1)+'}'
						curr_pkt=json.loads(payload)
						rx_count=rx_count+1
						psucc=rx_count/float(curr_pkt['n'])
						#print "{} : {}".format(rx_mac,psucc)
						res_data["t"]=float(t_now)
						res_data["rx"]=rx_count
						res_data["N"]=curr_pkt['n']
						res_val[str(rx_mac)]=res_data
						json_val = json.dumps(res_val)
						
			
			except (Exception) as err:
				if debug:
					print ( "exception", err)           
				pass
		if t_now - res_data["t"] > 1 and rx_count > 0:
			print json_val
			with open(out_file, "w" ) as myfile:
				myfile.write(json_val+"\n")
			json_val=""
			rx_count=0
			res_data={}
			res_data["t"]=float(time.time())
			res_data["rx"]=rx_count;
			res_data["N"]=0


def send_ctrl_msg(iface,json_data):
        a=RadioTap()/Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=my_mac, addr3="ff:ff:ff:ff:ff:ff")/json_data
        sendp(a, iface=mon_iface,verbose=0)


def usage(in_opt,ext_in_opt):
	print("input error: here optionlist: \n{0} --> {1}\n".format(in_opt,str(ext_in_opt)))




def send_probes(iface="wlan0",n=100):
	sleep_time=0
	for i in range(0,n):
		pkt_to_send={}
		pkt_to_send['seq']=i+1
		pkt_to_send['n']=n
		json_data = json.dumps(pkt_to_send)
		
		send_ctrl_msg(iface,json_data)
		if sleep_time > 0:
			time.sleep(sleep_time - ((time.time() - starttime) % sleep_time))


def main():
	ext_in_opt=["help", "iface=","tdelay=", "iperf_rate=", "enable_rxprobe=", "--output_path"];
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
	enable_rxprobe=False

	for o, a in opts:
	    if o in ("-i", "--iface"):
		iface = a
	    if o  in ("-t", "--tdelay"):
	       i_time = float(a)
	    if o  in ("-r", "--iperf_rate"):
	       iperf_rate = float(a)
	    if o  in ("-e", "--enable_rxprobe"):
	       enable_rxprobe=True
	    if o  in ("-o", "--output_path"):
		data_path=str(a)
	    elif o in ("-h", "--help"):
		usage()
		sys.exit()
	#INIT REACT INFO
	init(iface)

	if enable_rxprobe:
		send_probes()
	else:
		thread.start_new_thread( sniffer_probes,(iface,0.1,data_path ) )
		while 1:	
			pass

	
if __name__ == "__main__":
    main()
