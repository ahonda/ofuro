import logging

from lib.proto.pkt_proto import *
from lib.record.flow_record import File_Write_Flow, File_Delete_Flow

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

    def set_flow(self, flow, e_type):

        dpid = dpid_lib.dpid_to_str(self.dp.id)

        try:
            ofctl_v1_3.mod_flow_entry(self.dp, flow, ofproto_v1_3.OFPFC_ADD)
#            File_Write_Flow(dpid, flow, e_type)
        except:
            return

    def delete_flow(self, flow, e_num=0):

        dpid = dpid_lib.dpid_to_str(self.dp.id)
#        del_flow = File_Delete_Flow(dpid, flow, e_num)

        if flow != "{}":
            ofctl_v1_3.mod_flow_entry(self.dp, flow, ofproto_v1_3.OFPFC_DELETE)
