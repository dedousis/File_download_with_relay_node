#
#
#
#Atzamis Iosif, 3094
#Dedousis Andreas , 3018
#Kardoulakis Nikos, 3086
#
#



import socket
import sys
import random
import pickle
import os
import re
import subprocess
import urllib
import time
from Crypto import Random
from Crypto.Cipher import AES
import smtplib

def email_authentication():
    gmail_user = 'something@gmail.com'
    gmail_password = 'password'

    from_=gmail_user
    to =['receiver@gmail.com','receiver@gmail.com']
    code=(random.randint(1000,50000))
    email_text ="Once you receive the code.\n Enter the verification code: "+str(code)
    subject='AUTHENTICATION'
    message='Subject: %s\n\n %s'%(subject,email_text)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(from_,to,message)
        server.close()
        print("AUTHENTICATION SEND ")
        return code
    except:
        print 'Something went wrong...'
            

    

def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

def encrypt(message, key, key_size=256):
    message = pad(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(message)
                    
def encrypt_file(file_name, key):
    with open(file_name, 'rb') as fo:
        plaintext = fo.read()
    enc = encrypt(plaintext, key)
    with open(file_name + ".enc", 'wb') as fo:
        fo.write(enc)
############
        #       ping :
        #
        #       Argument num :
        #       Argument ip2 :
        #
        #       return argument info :
        #
############


def ping(num, ip2):
    ping_response = subprocess.Popen(["/bin/ping",str(ip2), "-c%d"%num, "-w100"],stdout=subprocess.PIPE).stdout.read()
    traceroute=subprocess.Popen(["traceroute", "-w100",str(ip2)],stdout=subprocess.PIPE)
    hops=sum(1 for _ in iter(traceroute.stdout.readline,""))
    hops= hops-1
    RTT = re.search("time=(.*) ms",str(ping_response))
    direct_RTT = float(RTT.group(1))
    info = {}
    info[0] = direct_RTT
    info[1] = int(hops)
                                 
    return info


############
        #
        #       download :
        #
        #
        #
############


def download(url):
    url=url.replace(" ",'')
    end_file=url[-4:]
    key = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'
    start_time = time.clock()
    urllib.urlretrieve(url,'file_relay_to_end'+end_file)
    #urllib.urlretrieve('https://www.youtube.com/yt/brand/media/image/YouTube-logo-full_color.png', 'file_relay.png')
    print('File downloaded in %s sec' % str(time.clock() - start_time))
    encrypt_file('file_relay_to_end'+end_file,key)            
    return key

RECV_BUFFER_SIZE = 1024
port= random.randint(1024,49151)
b=""
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (socket.gethostbyname(socket.gethostname()), int(port))
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    
    try:
        print >>sys.stderr, 'connection from', client_address
    
        # Receive the data in small chunks and retransmit it
        while True:
            data =connection.recv(RECV_BUFFER_SIZE)
            #print >>sys.stderr, 'received "%s"' % data[0]
            b+=data
            if  data:
                received=pickle.loads(b)
                end_server_ip = received[0]
                user_ping=received[1]
                down=received[2]
                url=received[3]
                if down==0:
                    data=ping(user_ping,end_server_ip)
                    HOPS=int(data[1])
                    RTT=float(data[0])
                    #print("PING to endserver\n")
                    #print("HOPS: %d"%HOPS)
                    #print("RTT: %f\n"%RTT)
                    connection.sendall(pickle.dumps(data))
                else:
                    key=download(url)
                    password=email_authentication()
                    connection.send(key)
                    connection.send(str(password))                    
                    end_file=url.replace(" ",'')
                    end_file=end_file[-4:]
                    with open('file_relay_to_end'+end_file+'.enc','rb')as myfile:
                        l=myfile.read()
                    size=len(l)
                    connection.send(str(size))
                    connection.sendall((l))

                    os.remove('file_relay_to_end'+end_file+'.enc')
                    os.remove('file_relay_to_end'+end_file)
            else:
                print >>sys.stderr, 'no more data from', client_address
                b=""
                break
    finally:
        # Clean up the connection
        connection.close()
