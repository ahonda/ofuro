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


class FlowCtl(object):
    def __init__(self, dp):

        self.dp = dp

    def set_flow(self, flow={}, e_type=0):

        dpid = dpid_lib.dpid_to_str(self.dp.id)

        try:
            ofctl_v1_3.mod_flow_entry(self.dp, flow, ofproto_v1_3.OFPFC_ADD)
        except:
            return

    def delete_flow(self, flow={}, e_num=0):

        dpid = dpid_lib.dpid_to_str(self.dp.id)

        ofctl_v1_3.mod_flow_entry(self.dp, flow, ofproto_v1_3.OFPFC_DELETE)
