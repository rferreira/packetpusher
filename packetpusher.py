#!/usr/bin/env python
"""
Packet Pusher - Network speed tester
Author: Rafael Ferreira <raf@ophion.org>
License: MIT/X11

TODO:
 * Add version validation section
 * Add packet ordering and checksumming

"""

import socket
import sys
import optparse
import time
import struct
import asyncore
import logging
import threading
import multiprocessing
from collections import deque
import prettytable



# General Variables
DEFAULT_PORT = 9999
DEFAULT_HOST = "127.0.0.1"
VERSION="0.4"
PROTOCOL_VERSION=2
LOG_FORMAT = '[%(asctime)s] [%(processName)s] %(levelname)s: %(message)s'

DESC= "Packet Pusher - Network speed tester"
log = logging.getLogger('pp')


class TBucket(object):
    """ Simple wrapper objects for storing test run telemetry"""
    
    BYTES_IN = 0
    BYTES_OUT = 1
    PACKETS_OUT = 2
    START_TIME = 3
    END_TIME = 4
    PACKETS_IN = 5
    
    def __init__(self):     
        self.store = [0.0] * 10
        
    def add(self, s):
        log.info('source:')
        log.info(s)
        log.info('self:')
        log.info(self)
            

    def time_elapsed(self):
        return round(self.store[TBucket.END_TIME] - self.store[TBucket.START_TIME],4)
        
    def transfer_rate(self, in_mega_bytes=True):
        tr = (self.store[TBucket.BYTES_OUT] + self.store[TBucket.BYTES_IN])/self.time_elapsed()
        
        if in_mega_bytes:
            return round(tr/1024.0/1024.0,2)
        
        return round(tr,2)
    
    def packets_out(self):
        return round(self.store[TBucket.PACKETS_OUT],2)

    def packets_in(self):
        return round(self.store[TBucket.PACKETS_IN],2)
        
    
    def mbytes_in(self):
        return round(self.store[TBucket.BYTES_IN]/1024/1024,2)
        
    def mbytes_out(self):
        return round(self.store[TBucket.BYTES_OUT]/1024/1024,2)
    
    def start(self):
            self.store[TBucket.START_TIME] = time.time()

    def get_start(self):
        return self.store[TBucket.START_TIME]

    def get_end(self):
        return self.store[TBucket.END_TIME]

    def end(self):
        self.store[TBucket.END_TIME] = time.time()
        
    def packet_transfer_rate(self):
        return round((self.store[TBucket.PACKETS_OUT] + self.store[TBucket.PACKETS_IN])/self.time_elapsed(),2)
    
    def add(self, tb):
        
        # list comprehension magic  
        tmp = [ sum(p) for p in zip(self.store,tb.store) ]

        # dealing intelligently with time       
        tmp[TBucket.START_TIME] = tb.get_start() if tb.get_start() < self.get_start() or self.get_start() == 0.0 else self.get_start()
        tmp[TBucket.END_TIME] = tb.get_end() if tb.get_end() > self.get_end() or self.get_end() == 0.0 else self.get_end()

        self.store = tmp
                        
class Packet:
    """
    16 bytes wide (unsigned ints):
    header format:
    0-3 Request ID 
    4-7 Sequence number 
    8-11 Total number of datagrams in this message 
    12-15 command
    16-1023 - data (string)
    """
    format = "!4I1008s"
    size = struct.calcsize(format)

    # commands:
    SYN  = 0
    ACK = 1
    START = 2
    END = 3 
    
    def __init__(self, sequence, total, data='', command = 0):
        self.data = data
        self.command = command
        self.total = total
        self.sequence = sequence
        self.id = sequence # for now
        
    def pack(self):
        """ returns a string representation of the packet ready for sending """
        return(struct.pack(self.format, self.id, self.sequence, self.total, self.command, self.data ))
        
    def unpack(self,data):
        """ parses the raw data stream and populates the control packet object"""
        t = struct.unpack(self.format,data)
        self.id = t[0]
        self.sequence = t[1]
        self.total = t[2]
        self.command = t[3]
        self.data = t[4]

    @staticmethod
    def from_bytes(data):
        packet = Packet(0,0,0,None)
        packet.unpack(data)
        return packet
        
    def __repr__(self):
        return 'packet: [%d] sequence: %d command %d total: %d data: [%s]' % (self.id, self.sequence, self.command,self.total, self.data[:3])
    
class Node(asyncore.dispatcher):
    """
    Handles all network io
    """
    def __init__(self, host, port, client=False):
        
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
                
        self.packets_sent = 0
        self.packets_rcv = 0
        self.bytes_sent = 0
        self.bytes_rcv = 0

        self.stats = TBucket()
        self.stats.start()

        # io buffers
        self.buffer_in = deque()
        self.buffer_out = deque()

        if client is True:
            self.set_reuse_addr()
            self.connect((host, port))

        else:
            self.bind((host, port))
            log.info("Server started on %s:%s" %  (self.addr) )
            # server monitoring thread:
            t = threading.Thread(target=self.status_thread)
            t.setDaemon(True)
            t.start()
        
        self.event = threading.Event()
                
    def handle_read(self):
        data, addr = self.recvfrom(1024)
        if not data:
            self.close()
            return

        self.packets_rcv += 1
        self.bytes_rcv += len(data)

        # parsing packet
        packet = Packet.from_bytes(data)

        if packet.command == Packet.START:
            log.info('new test session from: %s:%d' % addr)
                    
        elif packet.command == Packet.END:
            log.info('ending test session from: %s:%d' % addr)

    def handle_close(self):
        pass

    def handle_connect(self):
        pass
        
    def handle_accept(self):
        pass

    def handle_write(self):
        while len(self.buffer_out) > 0:
            packet = self.buffer_out.popleft()
            s = self.socket.send(packet.pack())
            self.packets_sent += 1
            self.bytes_sent += s            
        
        #log.info('flushing event')
        self.event.set()
            
    def writable(self):
        if len(self.buffer_out) > 0:
            return 1
            
    def handle_error(self):
        log.exception(sys.exc_value)

    def start(self):
        self.running = True
        while self.running:
            asyncore.loop(timeout=0.5, use_poll=False, count=1)         

    def stop(self):
        self.running = False
        self.stats.end()
        log.info('network node stopped')
        
    def send(self,packet, flush = False):
        self.buffer_out.append(packet)
        
        if len(self.buffer_out) > 50000 or flush is True:   
            log.debug('buffer full, pausing io')                
            self.event.clear()
            self.event.wait()       
    
    def status_thread(self):
        while 1:
            time.sleep(30)
            log.info('packets in: %d packets out: %d uptime: %d sec' % (self.packets_rcv, self.packets_sent,  time.time() - self.stats.get_start() ))

        

def worker(node):
    node.start()
                    
def packet_pusher(host_address,host_port,packet_count, results, start_event,timeout):           
    node = Node(host=host_address,port=host_port, client=True)
    t = threading.Thread(target=worker, name='node',args=(node,))
    t.setDaemon(True)
    t.start()
    
    # waiting for the go-ahead:
    log.info('started, waiting on go-head')
    
    start_event.wait()
    
    r = TBucket()
    r.start()
    
    seq = 0
    node.send(Packet(seq, packet_count, command=Packet.START), flush=True)
    
    # neva, neva neva use range() for this
    while True:
        node.send(Packet(seq,packet_count,data= 'x' * 1000))        

        if packet_count > 0 and seq == packet_count or time.time() - r.get_start() > timeout:
            break               
                        
        seq += 1
    
    # sending last packet
    node.send(Packet(seq+1, packet_count, command=Packet.END), flush=True)
                    
    # end clock
    r.end()

    # data structures:
    r.store[TBucket.BYTES_IN] = node.bytes_rcv
    r.store[TBucket.BYTES_OUT] = node.bytes_sent
    r.store[TBucket.PACKETS_IN] = node.packets_rcv
    r.store[TBucket.PACKETS_OUT] = node.packets_sent

    node.stop() 
    results.append(r)
    
def main():
    if len(sys.argv) == 1:
        sys.argv.append('-h')
        
    parser = optparse.OptionParser(description=DESC,version=VERSION)

    parser.add_option("-s","--server", dest="server", help="runs in server mode", action="store_true", default=False)
    parser.add_option("-c","--client", dest="client", help="runs in client mode", action="store_true", default=False)
    parser.add_option("-v","--verbose", dest="verbose", help="runs in verbose mode", action="store_true", default=False)
    parser.add_option("-p","--port", dest="port", help="the port to use for the data transfer", action="store")
    parser.add_option("-a","--address", dest="address", help="the name/ip to listen on (if server) or to send to (if client)", action="store")
    
    
    # client only options
    client_options = optparse.OptionGroup(parser,"Client options")
    client_options.add_option("-n","--packet-count", action="store", dest="packet_count", help="number of packets to send before quitting", default=10000000)
    client_options.add_option("-w","--workers", action="store", dest="num_workers", help='overwrites the default number of workers - number of cpus -1', default=0)
    client_options.add_option('-t','--timeout', action="store", type='int', dest="timeout", help='stops the test after n seconds', default=0) 
        
    parser.add_option_group(client_options)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT,datefmt='%m/%d/%Y %H:%M:%S')
    handler.setFormatter(formatter)     
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    
    (options,args) = parser.parse_args()

    host_address, host_port  = DEFAULT_HOST,DEFAULT_PORT    
    num_workers = multiprocessing.cpu_count() -1
    packet_count = int(options.packet_count)    
    
    if options.verbose:
        log.info('running in verbose mode')
        log.setLevel(logging.DEBUG) 
        
    if options.port is not None:
        host_port = options.port
    
    if options.address is not None:
        host_address = options.address
            
    if options.num_workers > 0:
        num_workers = int(options.num_workers)
        log.info('using custom number of workers (%d)', num_workers)
    else:
        log.info('%d cpus available, will utilize %d processes' % (multiprocessing.cpu_count(), num_workers ))

    if options.server:
        node = Node(host=host_address,port=host_port, client=False)
        node.start()

    if options.client:  
        log.info('running in client mode')  

        if options.timeout > 0:
            log.info('test will run for %d seconds' % options.timeout )
            packet_count = 0

        else:
            log.info('test will stop after sending %d packets' % packet_count)  
        
        
        manager = multiprocessing.Manager()
        start_event = multiprocessing.Event()
        
        results = manager.list()
        workers = []
        
        for x in range( num_workers ):
            p = multiprocessing.Process(target=packet_pusher,name='process-%d' % x, args=(host_address,host_port,packet_count,results,start_event,options.timeout))
            p.start()
            
            # storing the process and the result bucket
            workers.append(p)
        
        time.sleep(5)
        log.info('all processes started, starting test in 5 seconds...')
        time.sleep(5)
        start_event.set()
        
        log.info('test running...')

        for p in workers:
            p.join()

                
        log.info('test if finished, tabulating telemetry')
                
        total = TBucket()

        # work is done calculating the results
        x = prettytable.PrettyTable([
            'worker',
            'data out MB',
            'data in MB',
            'rate MB/s',
            'packets out',
            'packets in',
            'packet/s',
            'seconds'                           
        ])
        for i in range(len(workers)):
            process = workers[i]
            result = results[i]
        
            x.add_row([
                process.name,
                result.mbytes_out(),
                result.mbytes_in(),
                result.transfer_rate(),
                result.packets_out(),
                result.packets_in(),
                result.packet_transfer_rate(),
                result.time_elapsed(),
            ])  
            
            total.add(result)
            
        # adding totals
        
        x.add_row([
            'total',
            total.mbytes_out(),
            total.mbytes_in(),
            total.transfer_rate(),
            total.packets_out(),
            total.packets_in(),
            total.packet_transfer_rate(),
            total.time_elapsed(),
        ])
            
        print('')   
        print('Results:')   
        print(x)

    
if __name__ == "__main__":
    main()

            
