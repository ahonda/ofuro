import logging
import json
import uuid

from lib.proto.pkt_proto import *

# -------------------------------
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------

from ryu.lib import dpid as dpid_lib
from function.arp import Arp_Flow, Arp_Request
from function.record import Read_Record, Write_Record


def Nat_Ready(ofsw, ofuro_nat_set, flag=0):

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
            new_uuid = uuid.uuid4().hex
            ofsw.ofuro_data.ArpEntry.update({new_uuid : arp_data})

            nat_part.update({"CLIENT_MAC":"", "ARP_UUID":new_uuid})
            nat_set.append(nat_part)
        

        # Find Client MAC Address
        for arp_req in nat_set:
            Arp_Request(ofsw, arp_req["SW_IP"],  arp_req["CLIENT_IP"],  arp_req["SW_PORT"])

        if flag == 0:
            new_entry = {"ENTRY":[], "FLAG":0}
            new_entry.update({"ENTRY":nat_set})
            new_uuid = uuid.uuid4().hex
            ofsw.ofuro_data.NatEntry.update({new_uuid : new_entry})

            Write_Record(ofsw, 0)
            return {new_uuid : new_entry}

        logging.info('  +++++++++++++++++++++++++++++++++++++++++++++++++')
        
        
def Nat_Flow_Add(ofsw, arp_pkt_set):

    srcip = arp_pkt_set["SRC_IP"]
    dstip = arp_pkt_set["DST_IP"]
    srcmac = arp_pkt_set["SRC_MAC"]
    dstmac = arp_pkt_set["DST_MAC"]

    find_flag = 0

    for nat_uuid, nat_entry in ofsw.ofuro_data.NatEntry.items():
        if find_flag == 1:
            break

        nat_flow = {
            'priority' : PRIORITY_IP_HANDLING,
            'match': {'eth_type': ether.ETH_TYPE_IP},
            'actions': []
        }

        for nat_data in nat_entry["ENTRY"]:

            logging.info("    [Nat_Flow_Add] nat_data : %s ", nat_data)


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
        

def Nat_Flow_Del(ofsw, del_uuid):

    logging.info('----------- NAT FLOW DELETE Starting : %s -----------', del_uuid)

    find_flag = 0

    for nat_uuid, nat_entry in ofsw.ofuro_data.NatEntry.items():

        if nat_uuid == del_uuid:

            for nat_data in nat_entry["ENTRY"]:
                
                del_uuid = nat_uuid

                nat_flow = {
                    'match': {'eth_type': ether.ETH_TYPE_IP}
                }

                nat_flow["match"].update({"ipv4_dst": nat_data["SW_IP"]})
                nat_flow["match"].update({"ipv4_src": nat_data["CLIENT_IP"]})
                nat_flow["match"].update({"in_port" : nat_data["SW_PORT"]})

                arp_flow = {
                    'match': {'eth_type': ether.ETH_TYPE_ARP}
                }
                    
                arp_flow["match"].update({"arp_tpa": nat_data["SW_IP"]})
                arp_flow["match"].update({"in_port": nat_data["SW_PORT"]})

                find_flag = find_flag + 1

                ofsw.flow_ctl.delete_flow(nat_flow)
                ofsw.flow_ctl.delete_flow(arp_flow)

                if find_flag == 2:
                    logging.info("[Nat_Flow_Del] uuid: %s", del_uuid)
                    del ofsw.ofuro_data.NatEntry[del_uuid]
                    Write_Record(ofsw, 0)
                    logging.info('------------------------------------------------')
                    return 0
    return 1
                        
