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


class OfuroData(object):
    def __init__(self, dp):

        self.dp = dp
        self.nat_entry = []
#
# self.nat_entry[{"ENTRY": "entry, "STATUS":0/1, }
#
#
#
#
#
#


    def set_nat_data(self, flow, e_type):

        dpid = dpid_lib.dpid_to_str(self.dp.id)
        
        try:
            ofctl_v1_3.mod_flow_entry(self.dp, flow, ofproto_v1_3.OFPFC_ADD)
            File_Write_Flow(dpid, flow, e_type)
        except:
            return

    def delete_flow(self, flow, e_num=0):

        dpid = dpid_lib.dpid_to_str(self.dp.id)
        del_flow = File_Delete_Flow(dpid, flow, e_num)

        if del_flow != "{}":
            ofctl_v1_3.mod_flow_entry(self.dp, del_flow, ofproto_v1_3.OFPFC_DELETE)
