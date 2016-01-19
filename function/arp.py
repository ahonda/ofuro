import logging

from lib.proto.pkt_proto import *
from ryu.ofproto         import ofproto_v1_3
from ryu.lib import mac as mac_lib
from function.packet_out import Send_Packet_Out

def Arp_Reply(ofsw, msg, header_list):

    # ARP packet handling.                                                                                          
    in_port = msg.match['in_port']
    src_ip = header_list[ARP].src_ip
    dst_ip = header_list[ARP].dst_ip
    srcip = ip_addr_ntoa(src_ip)
    dstip = ip_addr_ntoa(dst_ip)

    if src_ip == dst_ip:
    # GARP -> packet forward (normal)
        output = self.ofctl.dp.ofproto.OFPP_NORMAL
        Send_Packet_Out(in_port, output, msg.data)
        self.logging.info('Receive GARP from [%s].', srcip)
        self.logging.info('Send GARP (normal).')

    else:
        if header_list[ARP].opcode == arp.ARP_REQUEST:
            # ARP request to router port -> send ARP reply                                                          
            src_mac = header_list[ARP].src_mac
            dst_mac = ofsw.port_data[in_port].mac
            arp_target_mac = dst_mac
            output = in_port

            Send_Arp(ofsw, arp.ARP_REPLY,dst_mac, src_mac, dst_ip, src_ip, arp_target_mac, in_port, output)

            log_msg = '[ARP REQUEST] from [IP %s : MAC %s] to [port %s : IP %s]'
            logging.info(log_msg, srcip, src_mac, in_port, dstip, extra=ofsw.sw_id)
#            logging.info('Send ARP reply to [%s]', srcip,
#                             extra=ofsw.sw_id)

        elif header_list[ARP].opcode == arp.ARP_REPLY:
            src_mac = header_list[ARP].src_mac
            dst_mac = header_list[ARP].dst_mac

            #  ARP reply to router port -> suspend packets forward
            find_flag = 0

            for nat_entry in ofsw.ofuro_data.nat_entry:

                nat_flow = {
                    'priority' : PRIORITY_IP_HANDLING,
                    'match': {'eth_type': ether.ETH_TYPE_IP},
                    'actions': []
                }

                if find_flag == 1:
                    break

                for nat_data in nat_entry:
                    if nat_data["CLIENT_IP"] == src_ip and nat_data["SW_IP"] == dst_ip:
                        nat_data["CLIENT_MAC"] = src_mac

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
                logging.info( ">>>> SET NAT FLOW >>>> %s",  nat_flow)
                ofsw.flow_ctl.set_flow(nat_flow,0)



def Arp_Request(ofsw, src_ip, dst_ip, in_port=None):

        src_mac = ofsw.port_data[in_port].mac
        dst_mac = mac_lib.BROADCAST_STR
        arp_target_mac = mac_lib.DONTCARE_STR
        inport = ofsw.dpset.ofproto.OFPP_CONTROLLER
        output = in_port
        Send_Arp(ofsw, arp.ARP_REQUEST, src_mac, dst_mac, 
                 src_ip, dst_ip, arp_target_mac, inport, output)


def Send_Arp(ofsw, arp_opcode, src_mac, dst_mac,
             src_ip, dst_ip, arp_target_mac, in_port, output):
    # Generate ARP packet                                                                                        
    ether_proto = ether.ETH_TYPE_ARP
    hwtype = 1
    arp_proto = ether.ETH_TYPE_IP
    hlen = 6
    plen = 4

    pkt = packet.Packet()
    e = ethernet.ethernet(dst_mac, src_mac, ether_proto)
    a = arp.arp(hwtype, arp_proto, hlen, plen, arp_opcode,
           src_mac, src_ip, arp_target_mac, dst_ip)

    pkt.add_protocol(e)
    pkt.add_protocol(a)
    pkt.serialize()
    # Send packet out                                                                                          
    Send_Packet_Out(ofsw, in_port, output, pkt.data, data_str=str(pkt))



def Arp_Flow(ofsw, arp_data, FLAG):

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

        arp_port = arp_value

        if arp_port != 0:
            flow_entry["match"].update({"in_port": arp_port })

        if FLAG == 0:
            ofsw.flow_ctl.set_flow(flow_entry, 0)
        else:
            ofsw.flow_ctl.delete_flow(flow_entry)
            

def ip_addr_ntoa(ip):
    return socket.inet_ntoa(addrconv.ipv4.text_to_bin(ip))


def mask_ntob(mask, err_msg=None):
    try:
        return (UINT32_MAX << (32 - mask)) & UINT32_MAX
    except ValueError:
        msg = 'illegal netmask'
        if err_msg is not None:
            msg = '%s %s' % (err_msg, msg)
        raise ValueError(msg)

def ipv4_text_to_int(ip_text):
    if ip_text == 0:
        return ip_text
    assert isinstance(ip_text, str)
    return struct.unpack('!I', addrconv.ipv4.text_to_bin(ip_text))[0]
