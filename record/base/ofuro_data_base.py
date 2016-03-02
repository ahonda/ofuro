import logging
import json

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

        ret_entry = {}
        all_entry =[]

        if uuid == "":

            logging.info('[ALL NAT ENTRY RETURN]')

            for nat_uuid, nat_entry in self.NatEntry.items():

                ret_entry.update({"NAT_ID":nat_uuid})

                for entry_key, entry_data in nat_entry.items():
                    ret_entry.update({entry_key:entry_data})

                all_entry.append(ret_entry)

        elif self.NatEntry.has_key(uuid) == True:
             ret_entry.update({"NAT_ID":uuid})
             for entry_key, entry_data in self.NatEntry[uuid].items():
                 ret_entry.update({entry_key:entry_data})

             all_entry.append(ret_entry)

        return all_entry


    def get_arp_entry(self, uuid=""):
        if uuid == "":
            logging.info('[ALL ARP ENTRY RETURN]')
            return self.ArpEntry

        else:
             ret_entry = {uuid: self.ArpEntry.get(uuid, None)}
             return ret_entry


