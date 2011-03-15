import socket
import sys
import optparse
import time
import struct
import asyncore
import logging, locale
import threading, multiprocessing
from collections import deque

from packetpusher.telemetry import TBucket
from packetpusher.protocol import Packet

log = logging.getLogger('pp')
            
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
        
    def send(self,packet, flush=False):
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
                    
# Helper functions:

def start_server(host, port):
    node =  Node(host,port,client=False)
    node.start()

def _process(host_address,host_port,packet_count, results, start_event,timeout):           
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

        
def start_client(host_address, host_port, num_workers, packet_count, timeout):   
    """
    start_client(host_address, host_port, num_workers, packet_count, options.timeout)   
    """        
    manager = multiprocessing.Manager()
    start_event = multiprocessing.Event()

    results = manager.list()
    workers = []

    for x in range( num_workers ):
        p = multiprocessing.Process(target=_process,name='process-%d' % x, args=(host_address,host_port,packet_count,results,start_event,timeout))
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

    return results