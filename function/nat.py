import logging
import json

from lib.proto.pkt_proto import *

# -------------------------------
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------

from ryu.lib import dpid as dpid_lib
from function.arp import Arp_Flow, Arp_Request
from function.record import Read_Record, Write_Record


def Nat_Ready(ofsw, ofuro_nat_set):

        logging.info('  +++++++++++++ NAT FLOW SET Ready  +++++++++++++')

        nat_set = []

        for nat_entry in ofuro_nat_set:
            nat_part = {}

            if nat_entry["SW_IP"] == "" or nat_entry["SW_PORT"] == "" or nat_entry["CLIENT_IP"] == "":
                logging.info('     ======= NAT ENTRY [%s] NO DATA ======')
                logging.info('  +++++++++++++++++++++++++++++++++++++++++++++++++')
                return
                
            nat_part.update({"SW_IP":nat_entry["SW_IP"]})
            nat_part.update({"SW_PORT":nat_entry["SW_PORT"]})
            nat_part.update({"CLIENT_IP":nat_entry["CLIENT_IP"]})

            arp_data = {nat_part["SW_IP"] : nat_part["SW_PORT"] }

            # Packet In Flow Set For ARP Packet 
            Arp_Flow(ofsw, arp_data, FLAG=0)

            nat_part.update({"CLIENT_MAC":"", "STAT":0})
            nat_set.append(nat_part)
        
        ofsw.ofuro_data.nat_entry.append(nat_set)

        # Find Client MAC Address
        for arp_req in nat_set:
            Arp_Request(ofsw, arp_req["SW_IP"],  arp_req["CLIENT_IP"],  arp_req["SW_PORT"])

        Write_Record(ofsw, 0)
        logging.info('  +++++++++++++++++++++++++++++++++++++++++++++++++')

def Nat_Flow_Add(ofsw, arp_pkt_set):

    srcip = arp_pkt_set["SRC_IP"]
    dstip = arp_pkt_set["DST_IP"]
    srcmac = arp_pkt_set["SRC_MAC"]
    dstmac = arp_pkt_set["DST_MAC"]

    find_flag = 0

    for nat_entry in ofsw.ofuro_data.nat_entry:
        if find_flag == 1:
            break

        nat_flow = {
            'priority' : PRIORITY_IP_HANDLING,
            'match': {'eth_type': ether.ETH_TYPE_IP},
            'actions': []
        }

        for nat_data in nat_entry:
            if nat_data["CLIENT_IP"] == srcip and nat_data["SW_IP"] == dstip:
                nat_data["CLIENT_MAC"] = srcmac
                nat_flow["actions"].append({"type": "SET_FIELD", "field": "eth_src","value": ofsw.port_data[nat_data["SW_PORT"]].mac })
                nat_flow["actions"].append({"type": "SET_FIELD", "field": "eth_dst","value": nat_data["CLIENT_MAC"] })
                nat_flow["actions"].append({"type": "SET_FIELD", "field": "ipv4_src","value": nat_data["SW_IP"] })
                nat_flow["actions"].append({"type": "SET_FIELD", "field": "ipv4_dst","value": nat_data["CLIENT_IP"] })
                nat_flow["actions"].append({"type": "OUTPUT", "port": nat_data["SW_PORT"] })
                find_flag = 1

            else:
                nat_flow["match"].update({"ipv4_dst": nat_data["SW_IP"]})
                nat_flow["match"].update({"ipv4_src": nat_data["CLIENT_IP"]})
                nat_flow["match"].update({"in_port" : nat_data["SW_PORT"]})


    if find_flag == 1:
        logging.info("    [NAT FLOW] PORT: %s SWIP: %s CLIENT %s", 
                     nat_flow["match"]["in_port"],
                     nat_flow["match"]["ipv4_dst"],
                     nat_flow["match"]["ipv4_src"] )

        ofsw.flow_ctl.set_flow(nat_flow,0)

def Nat_Flow_Del(ofsw, del_nat_set):

    logging.info('----------- NAT FLOW DELETE Starting -----------')
    del_port = []
    del_swip = []
    del_clip = []

    for del_entry in del_nat_set:
        del_port.append(del_entry["SW_PORT"])
        del_swip.append(del_entry["SW_IP"])
        del_clip.append(del_entry["CLIENT_IP"])


    find_flag = 0

    for entry_index, nat_entry in enumerate(ofsw.ofuro_data.nat_entry):

        for nat_data in nat_entry:
                
            now_swip = nat_data["SW_IP"]

            if now_swip in del_swip:
                
                nat_flow = {
                    'match': {'eth_type': ether.ETH_TYPE_IP}
                }

                num = del_swip.index(nat_data["SW_IP"])

                nat_flow["match"].update({"ipv4_dst": del_swip[num]})
                nat_flow["match"].update({"ipv4_src": del_clip[num]})
                nat_flow["match"].update({"in_port" : del_port[num]})

                arp_flow = {
                    'match': {'eth_type': ether.ETH_TYPE_ARP}
                }

                arp_flow["match"].update({"arp_tpa": del_swip[num]})
                arp_flow["match"].update({"in_port": del_port[num]})

                find_flag = find_flag + 1

                ofsw.flow_ctl.delete_flow(nat_flow)
                ofsw.flow_ctl.delete_flow(arp_flow)

                if find_flag == 2:
                    del ofsw.ofuro_data.nat_entry[entry_index]
                    Write_Record(ofsw, 0)
                    logging.info('------------------------------------------------')
                    return

