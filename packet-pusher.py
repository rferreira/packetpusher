#!/usr/bin/env python
"""
Packet Pusher - Network speed tester
Author: Rafael Ferreira <raf@ophion.org>
Copyright: GPL

TODO:
 * Add version validation section
 * Add packet ordering and checksumming

"""

import socket
import sys
import optparse
import time
import gc
import struct


# General Variables

DEFAULT_PORT = 9999
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PAYLOAD = 1024 # in bytes
RECEIVE_BUFFER = 1024
MAX_PACKETS = 100000
VERSION="0.1a"
PROTOCOL_VERSION=1

DESC= "Packet Pusher - Network speed tester"


class ControlPacket(object):
	""" Special packet used to send test run information from client to server """

	format = "3l17s"
	size = struct.calcsize(format)

	def __init__(self):
		pass
	
	def set(self,packet_size, packet_count, client_info):
		self.packet_size = packet_size
		self.packet_count = packet_count
		self.protocol_version  = PROTOCOL_VERSION
		self.client_info = client_info

	def pack(self):
		""" returns a string representation of the packet ready for sending """
		return(struct.pack(self.format,self.packet_size,self.packet_count,self.protocol_version,self.client_info ))
	def unpack(self,data):
		""" parses the raw data stream and populates the control packet object"""
		t = struct.unpack(self.format,data)
		self.packet_size = t[0]
		self.packet_count = t[1]
		self.protocol_version = t[2]
		self.client_info = t[3]

	def __str__(self):
		str = "Test options {\n"
		str += "\tPacket size: %d\n" % self.packet_size
		str += "\tPacket count: %d\n" % self.packet_count
		str += "\tProtocol version: %d\n" % self.protocol_version
		str += "\tClient info: %s\n" % self.client_info
		str += "}\n"
		return(str)



		
		
class InfoBucket(object):
	""" Simple wrapper objects for storing test run telemetry"""
	pass

class EndPoint(object):
		socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class PacketProducer(EndPoint):
	""" 
	Client side logic
	"""
	def __init__(self, addr, size, count):
	
		
		self.addr = addr
		self.count = count
		self.size = size
		
		# configuring send buffer size
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, size)

		self.payload = "X" * size
		self.socket.connect(addr)


	
	def start(self):
		""" start control logic and runs the test"""

		# control logic:
		cp = ControlPacket()
		cp.set(self.size,self.count,socket.gethostname())


		print("negotiating test with server...")
		# print(cp)

		try:
			# print(pickle.dumps(test_options))
			self.socket.send(cp.pack())

		except 	Exception,e:
			print("Sorry but a test run could not be negotiated with the server. Reason:")
			print(e)
			sys.exit(1)

	
		
		print("starting to send packets")

		counter = 1 
		bytes_sent = 0

		while(True):

			if (counter > self.count):
				break

			print '.',
			self.socket.send(self.payload)
			counter = counter +1
	
		print("")
		print("test done, check server for stats!")
		sys.exit(0)
		




class PacketConsumer(EndPoint):
	""" Server side logic """

	def __init__(self, addr):

		self.addr = addr
		self.socket.bind(addr)


	def start(self):
		
		
		print("Packet pusher server started on %s:%s" %  (self.addr) )

		# default_buffer = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

		while(1):
			print("")
			print("Waiting for client connections")
			print("")

			# self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, default_buffer )
			self.socket.settimeout(None)

			# handling control:
			test_options = ControlPacket()
			test_options.unpack(self.socket.recv(ControlPacket.size))

			if test_options is not None:
				print("Run options:")
				print(test_options)

				r = InfoBucket()

				# data structures:
				r.bytes_rcv = 0
				r.packets_rcv = 0
				r.packet_count = int(test_options.packet_count)
				r.packet_size = int(test_options.packet_size)

				
				# configuring rcv buffer size
				# this have been disabled because it somehow decreases performance
				# self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, r.packet_size)

				# after 5 inactive seconds we give up on the test
				self.socket.settimeout(5)

				# disabling the gc
				gc.disable()

				# Test run starting:
				r.start_time = time.time()
				while( r.packets_rcv < r.packet_count ):
				
					try: 
						data, addr  = self.socket.recvfrom(r.packet_size)
						r.bytes_rcv += len(data)
						r.packets_rcv += 1
						print '.',
						
						# we always set the stop time to the last 
						# received packet 
						r.stop_time = time.time()
					except socket.timeout:
						break

				
				gc.enable()

				# test done
				self._print_results(r)

	def _print_results(self,i):
		""" where i is a InfoBucket object used to store test run telemetry data"""

		# calculations
		success_percent = i.packets_rcv/float(i.packet_count) * 100
		
		time_elapsed = i.stop_time - i.start_time
		tr = i.bytes_rcv/time_elapsed 
		tr = tr/1024.0 # in KB
		tr = tr/1024.0 # in MB
		
		kbytes = i.bytes_rcv/1024.0

		print("")
		print("Test results {")
		print("\tTotal Kbytes transfered: %d" % i.bytes_rcv)
		print("\tTotal packets received: %d" % i.packets_rcv)
		print("\tTotal time elapsed: %.2f seconds"% time_elapsed)
		print("\tUDP success percentage: %d" % success_percent)
		print("\tData throughput: %.2f MB/s" % tr)
		print("}")



# main

def main():
	
	parser = optparse.OptionParser(description=DESC,version=VERSION)

	parser.add_option("-s","--server", dest="server", help="runs in server mode", action="store_true", default=False)
	parser.add_option("-c","--client", dest="client", help="runs in client mode", action="store_true", default=False)
	parser.add_option("-p","--port", dest="port", help="the port to use for the data transfer", action="store")
	parser.add_option("-a","--address", dest="address", help="the name/ip to listen on (if server) or to send to (if client)", action="store")
	
	# client only options
	client_options = optparse.OptionGroup(parser,"Client options")
	client_options.add_option("-k","--packet-size", action="store", dest="packet_size", help="packet size in kbytes")
	client_options.add_option("-n","--packet-count", action="store", dest="packet_count", help="number of packets to send before quitting")
	parser.add_option_group(client_options)
	

	(options,args) = parser.parse_args()

	host_address, host_port, packet_size, packet_count = DEFAULT_HOST,DEFAULT_PORT,DEFAULT_PAYLOAD, MAX_PACKETS


	if options.port is not None:
		host_port = options.port
	
	if options.address is not None:
		host_address = options.address

	if options.packet_size is not None:
		packet_size = int(options.packet_size)*1024
	
	if options.packet_count is not None:
		packet_count = int(options.packet_count)

	if options.client:
		pp = PacketProducer( ( host_address, host_port), size=packet_size, count=packet_count )
		pp.start()

	elif options.server:

		pc = PacketConsumer( ( host_address, host_port))
		pc.start()

	

if __name__ == "__main__":
	main()

			
