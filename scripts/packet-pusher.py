#!/usr/bin/env python
"""
Packet Pusher - Network speed tester
Author: Rafael Ferreira <raf@ophion.org>
License: MIT/X11

TODO:
 * Add version validation section
 * Add packet ordering and checksumming

"""

import logging, sys, optparse
import prettytable
import multiprocessing

from packetpusher.core import start_server, start_client
from packetpusher.telemetry import TBucket
from packetpusher import __version__ as VERSION


log = logging.getLogger('pp')


# General Variables
DEFAULT_PORT = 9999
DEFAULT_HOST = "127.0.0.1"
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'

DESC= "Packet Pusher - Network speed tester"

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
    client_options.add_option("-n","--packet-count", action="store", dest="packet_count", help="number of packets to send before quitting", default=0)
    client_options.add_option("-w","--workers", action="store", dest="num_workers", help='overwrites the default number of workers - number of cpus -1', default=0)
    client_options.add_option('-t','--timeout', action="store", type='int', dest="timeout", help='stops the test after n seconds', default=60) 
        
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
        start_server(host=host_address,port=host_port)

    if options.client:  
        log.info('running in client mode')  

        if options.timeout > 0:
            log.info('test will run for %d seconds' % options.timeout )
            packet_count = 0

        else:
            log.info('test will stop after sending %d packets' % packet_count)  
        
       
        results = start_client(host_address, host_port, num_workers, packet_count, options.timeout)        
                
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
        for i in range(num_workers):            
            result = results[i]
        
            x.add_row([
                'process-' + str(i),
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

            
