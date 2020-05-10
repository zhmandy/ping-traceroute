from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
ICMP_TIME_EXCEEDED = 11
ICMP_ECHO_REPLY = 0
NUM_PACKETS = 3
MAX_HOPS = 30

def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = string[count+1] * 256 + string[count] 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + string[len(string) - 1]
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer 

def getPacket(mySocket, destAddr, ID):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	
	myChecksum = 0
	# Make a dummy header with a 0 checksum
	# struct -- Interpret strings as packed binary data
	header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
	# Calculate the checksum on the data and the dummy header.

	myChecksum = checksum(header + data) 
	
	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		# Convert 16-bit integers from host to network byte order
		myChecksum = htons(myChecksum) & 0xffff		
	else:
		myChecksum = htons(myChecksum)
		
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data

	return packet

def traceroute(host, timeout=1):
	# timeout=1 means: If one second goes by without a reply from the server,
	# the client assumes that either the client's ping or the server's pong is lost
	dest = gethostbyname(host)
	print("Tracing route to {} [{}] with Python & Raw Socket:".format(host, dest))
	print("over a maximum of {} hops:".format(str(MAX_HOPS)))
	print("")

	for ttl in range(1, MAX_HOPS):
		RTTs = []
		for j in range(NUM_PACKETS):
			RTTs.append("*")

		currentAddr = ""
		currentType = 0
		success = 0

		for i in range(NUM_PACKETS):
			# Make a raw socket named mySocket
			icmp = getprotobyname("icmp")
			mySocket = socket(AF_INET, SOCK_RAW, icmp)
			
			# Return the current process i
			myID = os.getpid() & 0xFFFF

			# setup socket
			mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
			mySocket.settimeout(timeout)
			
			try:
				packet = getPacket(mySocket, dest, myID)
				mySocket.sendto(packet, (host, 0))
				startedSelect = time.time()
				whatReady = select.select([mySocket], [], [], timeout)
				howLongInSelect = (time.time() - startedSelect)

				# select timeout
				if whatReady[0] == [] or howLongInSelect >= timeout:
					continue
					
				recvPacket, addr = mySocket.recvfrom(1024)
				timeReceived = time.time()
			
			# socket timeout
			except timeout:
				continue

			icmpHeader = recvPacket[20:28]
			request_type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
			
			databytes = struct.calcsize("d")
			timeSent = struct.unpack("d", recvPacket[28:28 + databytes])[0]
			
			currentAddr = addr[0]
			currentType = request_type

			if currentType == 11:
				RTT = int((timeReceived - startedSelect) * 1000)
			elif currentType == 0:
				RTT = int((timeReceived - timeSent) * 1000)

			RTTs[i] = str(RTT)
			success += 1

			mySocket.close()
			# one second
			time.sleep(1)
		
		if success != 0:
			print(" {:>2}".format(ttl), end =" ")
			for j in range(NUM_PACKETS):
				print("{:>10}".format(RTTs[j] + " ms"), end =" ")
			print("	{}".format(currentAddr))
		else:
			print(" {:>2}".format(ttl), end =" ")
			for j in range(NUM_PACKETS):
				print("{:>10}".format("*"), end =" ")
			print("	{}".format(currentAddr))
		
		if currentType == 0:
			print("")
			print("Trace comlete.")
			return

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print("USAGE: python .\Traceroute.py <website>")
		sys.exit(1)

	traceroute(sys.argv[1])