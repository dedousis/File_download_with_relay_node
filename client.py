#
#
#
#Atzamis Iosif, 3094
#Dedousis Andreas , 3018
#Kardoulakis Nikos, 3086
#
#


import os
import re
import subprocess
import urllib
import time
import socket
import sys
import pickle
import threading
import Queue
import random 
from Crypto import Random
from Crypto.Cipher import AES
import getpass


def password(info):
    pass_=getpass.getpass("Enter password : ")
    tries=0
    while tries<3:
        if pass_== info[1]:
            decrypt_file('file_received_from_relay'+info[2]+'.enc',info[0])
            print("Password Is Correct. File Decrypted")
            os.remove('file_received_from_relay'+info[2]+'.enc')
            break
        else:
            remain=3-tries
            tries+=1
            print("Wrong Password, %s tries left !!"%remain)
            pass_= getpass.getpass("Enter password : ")
            

def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return plaintext.rstrip(b"\0")
    
def decrypt_file(file_name, key):
    with open(file_name, 'rb') as fo:
        ciphertext = fo.read()
    dec = decrypt(ciphertext, key)
    with open(file_name[:-4], 'wb') as fo:
        fo.write(dec)

def relay_download(url,
    relay_ip,port,
    ip,user_ping,down):
    url=url.replace(" ",'')
    end_file=url[-4:]
    RECV_BUFFER_SIZE = 1024
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = (str(relay_ip), int(port))
    sock.connect(server_address)
    try:
        recvd=''
        # Send data
        message ={}
        message[0]=ip
        message[1]=user_ping
        message[2]=down
        message[3]=(url)
        print(message[3])
        sock.sendall(pickle.dumps(message))
        # Look for the response
        if down==1:
            key=sock.recv(RECV_BUFFER_SIZE)
            authentication = sock.recv(RECV_BUFFER_SIZE)
            size=int(sock.recv(RECV_BUFFER_SIZE))
            f=open('file_received_from_relay'+end_file+'.enc','wb')
            amount=0
            amount_exp=int(size)
            while amount<amount_exp:
                print("Receiving...")
                l=sock.recv(RECV_BUFFER_SIZE)
                recvd+=l
                amount+=len(l)
                
            f.write(recvd)
            print("Done\n")
            f.close()
            sock.shutdown(socket.SHUT_WR)
            #decrypt_file('file_received_from_relay.gif.enc',key)
    finally:
        sock.close()
    info={}
    info[0]=key
    info[1]=authentication
    info[2]=end_file
    return info



############
	# 	ping : 
	#		
	#	Argument num :	
	#	Argument ip2 :
	#	Argument direct :
	#
	#	return argument info :
	#
############

def ping(
	num,ip2,
	direct):
    ping_response = subprocess.Popen(["/bin/ping","-c%d"%num,"-w100",str(ip2)], stdout=subprocess.PIPE).stdout.read()
    traceroute=subprocess.Popen(["traceroute", "-w100",str(ip2)],stdout=subprocess.PIPE)
    hops=sum(1 for _ in iter(traceroute.stdout.readline,""))
    hops= hops-1
    RTT = re.search("time=(.*) ms",str(ping_response))
    direct_RTT = float(RTT.group(1))
    info = {}
    info[0] = direct_RTT
    info[1] = int(hops)
    
    if direct==1:
        print("Direct IP : %s"%ip2)
        print("Direct RTT : %s"%info[0])
        print("Direct HOPS : %s"%info[1])
        dict_IP_RTT[ip2]=info[0]
        dict_IP_HOPS[ip2]=info[1]
            
    return info

############
	#	
	#	download : 
	#
	#
	#
############

def download(url):
    url=url.replace(" ",'')
    end=url[-4:]
    start_time = time.clock()
    urllib.urlretrieve(str(url), 'file_client'+end)
    print('File downloaded in %s sec' % str(time.clock() - start_time))

############
	#
	#	connect_relay : 
	#
	#	Argument relay_ip : 
	#	Argument port :
	#	Argument user_ping : 
	#	Argument down :  
	#
	#	return received : 
	#
############

def connect_relay(url_down,
	relay_ip,port,ip,
	user_ping,down):


    relaydata=ping(user_ping,relay_ip,0)
    RTT_relay = float(relaydata[0])
    HOPS_relay = relaydata[1]
    print('RElAY IP: %s \n'%relay_ip)
    print('RTT_to_relay : %f' % RTT_relay)  # RTT
    print('HOPS_to_relay : %d\n' % HOPS_relay)  # HOPS
    
    
    RECV_BUFFER_SIZE = 1024

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_address = (str(relay_ip), int(port))
    sock.connect(server_address)

    try:
        b=''
        # Send data
        message ={}
        message[0]=ip
        message[1]=user_ping
        message[2]=down
        message[3]=url_down
        sock.sendall(pickle.dumps(message))
        # Look for the response
        if down==0:
            data=sock.recv(RECV_BUFFER_SIZE)
            b+=data
            received=pickle.loads(b)
    finally:
        #print >> sys.stderr, 'closing socket'
        sock.close()

    RTT_relay_end=float(received[0])
    HOPS_relay_end=int(received[1])
    print('RTT relay__to_end : %f' % RTT_relay_end)  # RTT
    print('HOPS relay_to_end : %d\n' % HOPS_relay_end)  # HOPS
    
    RTT_final=RTT_relay + RTT_relay_end
    HOPS_final=int(HOPS_relay + HOPS_relay_end)
    print('RTT final: %f'%RTT_final)
    print('HOPS final: %d'%HOPS_final)
    dict_IP_RTT[relay_ip]=RTT_final
    dict_IP_HOPS[relay_ip]=HOPS_final
        
    return received


#
#
#
#
#
#
#

def find_min_RTT(y):
    minimum={}
    min_ips_list_RTT= []
    num=len(dict_IP_RTT)
    keys=dict_IP_RTT.keys()
    ip_min=dict_IP_RTT.keys()[0]
    min=dict_IP_RTT[ip_min]
    for i in range(1,num):
        if dict_IP_RTT[keys[i]]<min :
            ip_min=keys[i]
            min=dict_IP_RTT[keys[i]]

    print("to mikrotero RTT to exei i IP: %s"%ip_min)
    for i in range(num):
        if dict_IP_RTT[keys[i]]==min and ip_min!=keys[i]:
            min_ips_list_RTT.append(keys[i])

    if len(min_ips_list_RTT)==0:
        if y==0:
            minimum[0]=ip_min
            minimum[1]=min
        else:
            print("Ginetai epilogi me basi to kritirio RTT")
            minimum[0]=ip_min
            minimum[1]=min

    else:
        if y==0:
            print("Call find_min_HOPS...")
            minimum=find_min_HOPS(1)
        else:
            print(" Ginetai tuxaia epilogi")
            tmp=random.randint(0,num-1)
            tmp_ip=keys[tmp]
            minimum[0]=tmp_ip
            minimum[1]=dict_IP_RTT[tmp_ip]
            print("I tuxaia ip einai : %s"%minimum[0])
            print("To tuxaio RTT einai : %s"%minimum[1])
                        
            
    return minimum
                                                                        

#
#
#
#
#

def find_min_HOPS(y):
    minimum={}
    min_ips_list_HOPS= []
    num=len(dict_IP_HOPS)
    keys=dict_IP_HOPS.keys()
    ip_min=dict_IP_HOPS.keys()[0]
    min=dict_IP_HOPS[ip_min]
    for i in range(1,num):
        if dict_IP_HOPS[keys[i]]<min :
            ip_min=keys[i]
            min=dict_IP_HOPS[keys[i]]
            
    print("to mikrotero HOPS to exei i IP: %s"%ip_min)
    for i in range(num):
        if dict_IP_HOPS[keys[i]]==min and ip_min!=keys[i]:
            min_ips_list_HOPS.append(keys[i])
            
                    
            
    if len(min_ips_list_HOPS)==0:
        if y==0:
            minimum[0]=ip_min
            minimum[1]=min
        else:
            print("Ginetai epilogi me basi to kritirio hops")
            minimum[0]=ip_min
            minimum[1]=min
                        
    else:
        if y==0:
            print("Call find_min_RTT...")
            minimum=find_min_RTT(1)
        else:
            print(" Ginetai tuxaia epilogi")
            tmp=random.randint(0,num-1)
            tmp_ip=keys[tmp]
            minimum[0]=tmp_ip
            minimum[1]=dict_IP_HOPS[tmp_ip]
            print("I tuxaia ip einai : %s"%minimum[0])
            print("To tuxaio HOPS einai : %s"%minimum[1])
                         

    return minimum
            

#----------------------------------------------File me alias kai IP-------------------------------------------------
arxeio=str(sys.argv[2])
file = open(arxeio, "r+")
dict = {}
for line in file:
    b = line.split(",")
    url = b[0]  # IP address
    alias = b[1]  # ALIAS
    alias=alias.replace(" ",'')
    if '\n' in alias:
        alias2 = alias[0:len(alias) - 1]
    else:
        alias2 = alias
    if '\r' in alias:
        alias3 = alias2[0:len(alias2) - 1]
    else:
        alias3 = alias2
    dict[alias3] = url

#print(dict)  # print dictionary
#print('-----------------------------------------------------------')
#--------------------------------------------File me Relays--------------------------------------------------------
arxeio2=str(sys.argv[4])
file2 = open(arxeio2, "r+")
dict_relaysIP_alias = {}
dict_relaysIP_port = {}
for line in file2:
    b = line.split(",")
    ip = b[1]  # IP address
    alias = b[0]  # ALIAS
    relay_port=b[2]
    if '\n' in relay_port:
        relay_port2 = relay_port[0:len(relay_port) - 1]
    else:
        relay_port2 = relay_port
    if '\r' in relay_port:
        relay_port3 = relay_port2[0:len(relay_port2) - 1]
    else:
        relay_port3 = relay_port2
    
    dict_relaysIP_alias[ip] = alias
    dict_relaysIP_port[ip] = relay_port3
#print(dict_relaysIP_alias)  # print dictionary
#print('--------------------------------------------')
#print(dict_relaysIP_port)
#-------------------------------------------------------------------------------------------------------
num_of_relays=len(dict_relaysIP_alias)

thread_list= []
q=Queue.Queue()
dict_IP_RTT = {}
dict_IP_HOPS = {}
#user_input= raw_input("Enter alias, ping, choice(latency/hops) \n").split(' ')
#user_alias=user_input[0]
#user_ping=int(user_input[1])
#choice=user_input[2]
while True:
    user_input= raw_input("Enter alias,"
				" ping,"
				" choice(latency/hops) \n").split(' ')
    user_alias=user_input[0]
    user_ping=int(user_input[1])
    choice=user_input[2]
    if(choice=="latency")or(choice=="hops"):
        break;
    else:
        print("Invalid input, enter again! \n")

url_down=raw_input("Enter url: ")                 
if user_alias in dict:
    x=dict[user_alias]
    ip2=socket.gethostbyname(x)
    print("ip: %s"%ip2)
    url = dict[user_alias]
    print("Url: %s"%url)
    t=threading.Thread(target=ping,args=(user_ping,ip2,1,))
    thread_list.append(t)

    keys=list(dict_relaysIP_alias.keys())
    #print(keys)
    for i in range(num_of_relays):
        print(dict_relaysIP_port[keys[i]])
        t=threading.Thread(target=connect_relay,args=(url_down,keys[i],dict_relaysIP_port[keys[i]],ip2,user_ping,0,))                     
        thread_list.append(t)
                
    for thread in thread_list:
        thread.start()

    for thread in thread_list:
        thread.join()
        
    print(dict_IP_RTT)
    print(dict_IP_HOPS)
    print("----------dict IP-RTT-----------\n")
    print(dict_IP_RTT)
    print("----------dict IP-HOPS-----------\n")
    print(dict_IP_HOPS)
    if choice=="latency":
        min=find_min_RTT(0)
        print("RTT MIN : %s"%min[1])
        print("IP min : %s"%min[0])
    elif choice=="hops":
        min=find_min_HOPS(0)
        print("HOPS MIN: %s"%min[1])
        print("IP min : %s"%min[0])

    print(min[0])
    if min[0]==ip2:
        print("------------Direct Download------------")
        download(url_down)
    else:
        print("-----------Download via relay----------")
        info=relay_download(url_down,min[0],dict_relaysIP_port[min[0]],ip2,user_ping,1)
        password(info)
else:
    print("Den vrethike alias")

