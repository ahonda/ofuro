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
from function.flow_record import Write_Record


def Nat_Ready(ofsw, ofuro_nat_set):

        logging.info('+++++++++++++++ NAT FLOW SET Starting +++++++++++++++')

        nat_set = []

        for nat_entry in ofuro_nat_set:
            nat_part = {}
            logging.info("NAT ENTRY >> %s ", nat_entry)


            if nat_entry["SW_IP"] == "" or nat_entry["SW_PORT"] == "" or nat_entry["CLIENT_IP"] == "":
                logging.info('     ======= NAT ENTRY [%s] NO DATA ======')
                logging.info('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
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


def Nat_Flow_Del(ofsw, del_nat_set):

    logging.info('--------------- NAT FLOW DELETE Starting -------------------')
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
                    logging.info("[find] %s", ofsw.ofuro_data.nat_entry)

                    del ofsw.ofuro_data.nat_entry[entry_index]
                    logging.info("[find] %s", ofsw.ofuro_data.nat_entry)

                    Write_Record(ofsw, 0)
                    return
