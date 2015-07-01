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
    def __init__(self, dp, ofuro_set):

        self.dp = dp
        self.ofuro_set = ofuro_set
        self.now_flows = {}

    def static_flow_set(self, flow_entry, flag=0):
        try:
            self.set_flow(flow_entry, 0)
        except:
            return

    def static_flow_del(self, flow_entry, e_num=0):

        try:
            self.delete_flow(flow_entry, e_num)
        except:
            return


    def arp_packet_in_flow(self, arp_data, flag=0):

        if flag == 0:
            arp_data =  self.ofuro_set.get("ARP")
            if arp_data == None:
                return
        elif flag == 1:
            pass
        elif flag == 2:
            pass

        flow_entry = {
            'priority' : PRIORITY_ARP_HANDLING ,
            'match': {
                'eth_type': ether.ETH_TYPE_ARP ,
            },
            'actions': [
                {
                    'type': 'OUTPUT',
                    'port': ofproto_v1_3.OFPP_CONTROLLER,
                },
            ],
        }

        for arp_key, arp_value in arp_data.iteritems():
            flow_entry["match"].update({"arp_tpa":arp_key})
            for port in arp_value["PORT"]:
                port = int(port)

                if port != 0:
                    flow_entry["match"].update({"in_port": port })


                if flag == 0:
                    print ">>> ARP P_IN Flow SET >>> [%s]  port: %d addr: %s" % (dpid_lib.dpid_to_str(self.dp.id), port, arp_key)
                    self.set_flow(flow_entry, 1)
                    self.ofuro_set["ARP"][arp_key].update({"flow_rule":flow_entry})
 
                elif flag == 1:
                    print ">>> ARP P_IN Flow ADD >>> [%s]  port: %d addr: %s" % (dpid_lib.dpid_to_str(self.dp.id), port, arp_key)
                    self.set_flow(flow_entry, 1)
                    self.ofuro_set["ARP"].update(arp_data)
                    self.ofuro_set["ARP"][arp_key].update({"flow_rule":flow_entry})
               
                elif flag == 2:
                    print ">>> ARP P_IN Flow DELETE >>> [%s]  port: %d addr: %s" % (dpid_lib.dpid_to_str(self.dp.id), port, arp_key)
                    self.delete_flow(flow_entry)
                    del self.ofuro_set["ARP"][arp_key]


    def set_flow(self, flow, e_type):

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
        

    def get_all_flow(self, waiters):
        ofp = self.dp.ofproto
        ofp_parser = self.dp.ofproto_parser

        match = ofp_parser.OFPMatch()
        stats = ofp_parser.OFPFlowStatsRequest(self.dp, 0, 0, ofp.OFPP_ANY, ofp.OFPG_ANY, 0, 0, match)

        self.dp.set_xid(stats)
        waiters_per_dp = waiters.setdefault(self.dp.id, {})
        msgs = self.dp.send_msg(stats)

        return msgs

