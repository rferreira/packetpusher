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

            
