import logging

from lib.proto.pkt_proto import *

# -------------------------------
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------

from ryu.lib import dpid as dpid_lib
from function.arp import Arp_Flow, Arp_Request


def Nat_Ready(ofsw, ofuro_nat_set):

        logging.info('+++++++++++++++ NAT FLOW SET Starting +++++++++++++++')

#        for nat_entry in ofuro_nat_set:

#            for k, v in nat_entry.items(): 
#                if v == "":
#                    logging.info('     ======= NAT ENTRY [%s] NO DATA ======', k)
#                    logging.info('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
#                    return

        nat_set = []

        for nat_entry in ofuro_nat_set:
            nat_part = {}

            for item_k, item_v in nat_entry.items():

                if item_v == "":

                    logging.info('     ======= NAT ENTRY [%s] NO DATA ======', k)
                    logging.info('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
                    return
                
                nat_part.update({item_k:item_v})


            arp_data = {nat_part["SW_IP"] : nat_part["SW_PORT"] }

            logging.info("   [ARP DATA] --> %s ", arp_data)

            # Packet In Flow Set For ARP Packet 
            Arp_Flow(ofsw, arp_data, FLAG=0)

            nat_part.update({"CLIENT_MAC":"", "STAT":0})
            nat_set.append(nat_part)
        
        ofsw.ofuro_data.nat_entry.append(nat_set)
        logging.info("**** [NAT DATA] --> %s ", ofsw.ofuro_data.nat_entry)

        # Find Client MAC Address
        for arp_req in nat_set:
            Arp_Request(ofsw, arp_req["SW_IP"],  arp_req["CLIENT_IP"],  arp_req["SW_PORT"])



def Nat_Flow_Del(ofsw, del_nat_set):

    logging.info('--------------- NAT FLOW DELETE Starting -------------------')
    del_port = []
    del_swip = []
    del_clip = []

    for del_entry in del_nat_set:
        del_port.append(del_entry["SW_PORT"])
        del_swip.append(del_entry["SW_IP"])
        del_clip.append(del_entry["CLIENT_IP"])


    logging.info("[PORT] %s [SW_IP] %s [CL_IP] %s", del_port, del_swip, del_clip)


    find_flag = 0

    for nat_entry in ofsw.ofuro_data.nat_entry:

        if find_flag == 2:
             break

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

                logging.info("[DELETE NAT FLOW] %s", nat_flow)
                ofsw.flow_ctl.delete_flow(nat_flow)
                logging.info("[DELETE ARP FLOW] %s", arp_flow)
                ofsw.flow_ctl.delete_flow(arp_flow)
