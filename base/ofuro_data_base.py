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

        self.NatEntry = {}
        self.ArpEntry = {}


    def get_nat_entry(self, uuid=""):
        if uuid == "":
            logging.info('[ALL NAT ENTRY RETURN]')
            return self.NatEntry

        else:
             ret_entry = {uuid: self.NatEntry.get(uuid, None)}
             return ret_entry


    def get_arp_entry(self, uuid=""):
        if uuid == "":
            logging.info('[ALL ARP ENTRY RETURN]')
            return self.ArpEntry

        else:
             ret_entry = {uuid: self.ArpEntry.get(uuid, None)}
             return ret_entry
