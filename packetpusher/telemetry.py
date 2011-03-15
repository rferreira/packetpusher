import logging, sys

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