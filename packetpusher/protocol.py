import logging, struct

log = logging.getLogger('pp')

PROTOCOL_VERSION=2

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