#!/usr/bin/env python
"""
Packet Pusher - Network speed tester
Author: Rafael Ferreira <raf@ophion.org>
Copyright: GPL

Please note:
	- 

TODO:
 * Add version validation section
 * Add packet ordering and checksumming

"""

import socket
import sys
import optparse
import pprint
import pickle
import time
import gc

# General Variables

DEFAULT_PORT = 9999
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PAYLOAD = 1024 # in bytes
RECEIVE_BUFFER = 1024
MAX_PACKETS = 100000
VERSION='0.1a'

DESC= "Packet Pusher - Network speed tester v%s" % VERSION

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
		test_options = { 
			'PACKET_SIZE': self.size,
			'PACKET_COUNT': self.count,
			'PROTOCOL_VERSION': VERSION,
			'CLIENT' : socket.gethostname()

		}


		print("negotiating test with server...")
		pprint.pprint(test_options)

		try:
			# print(pickle.dumps(test_options))
			self.socket.send(pickle.dumps(test_options))

		except 	Exception:
			print("Sorry but a test run could not be negotiated with the server")
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

		default_buffer = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

		while(1):
			print("")
			print("Waiting for client connections")
			print("")

			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, default_buffer )
			self.socket.settimeout(None)

			# handling control:
			data = self.socket.recv(1024)
			#print(data)
			test_options = pickle.loads(data)

			if test_options is not None:
				print("Run options:")
				pprint.pprint(test_options)

				r = InfoBucket()

				# data structures:
				r.bytes_rcv = 0
				r.packets_rcv = 0
				r.packet_count = int(test_options['PACKET_COUNT'])
				r.packet_size = int(test_options['PACKET_SIZE'])

				
				# configuring rcv buffer size
				self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, r.packet_size)

				# after 5 inactive seconds we give up on the test
				self.socket.settimeout(1)

				# Test run starting:
				r.start_time = time.time()

				# disabling the gc
				gc.disable()
				while( r.packets_rcv < r.packet_count ):
				
					try: 
						data = self.socket.recv(r.packet_size)
						r.bytes_rcv += len(data)
						r.packets_rcv += 1
						print '.',
					except socket.timeout:
						break

				gc.enable()

				# test done
				r.stop_time = time.time()
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
		print("")
		print("\tData throughput: %.2f MB/s" % tr)
		print("}")




		



# main

def main():
	
	parser = optparse.OptionParser(description=DESC)

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

			
