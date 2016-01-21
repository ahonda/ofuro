import logging

from lib.proto.pkt_proto import *

# -------------------------------
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------

from ryu.lib import ofctl_v1_3
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib


class OfuroData(object):
    def __init__(self, dp):

        self.dp = dp
        self.nat_entry = []
        self.arp_entry = []

