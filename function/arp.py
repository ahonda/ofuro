import logging
import json

from lib.proto.pkt_proto import *
from ryu.ofproto         import ofproto_v1_3
from ryu.lib import mac as mac_lib
from function.packet_out import Send_Packet_Out
from function.record import Read_Record, Write_Record


def Arp_Reply(ofsw, msg, header_list):

    # ARP packet handling.                                                                                          
    in_port = msg.match['in_port']
    src_ip = header_list[ARP].src_ip
    dst_ip = header_list[ARP].dst_ip
    srcip = ip_addr_ntoa(src_ip)
    dstip = ip_addr_ntoa(dst_ip)
    arp_pkt_set = {}

    if src_ip == dst_ip:
    # GARP -> packet forward (normal)
        output = self.ofctl.dp.ofproto.OFPP_NORMAL
        Send_Packet_Out(in_port, output, msg.data)
        self.logging.info('Receive GARP from [%s].', srcip)
        self.logging.info('Send GARP (normal).')

        retcode = "GARP"

    else:
        if header_list[ARP].opcode == arp.ARP_REQUEST:
            # ARP request to router port -> send ARP reply                                                          
            src_mac = header_list[ARP].src_mac
            dst_mac = ofsw.port_data[in_port].mac
            arp_target_mac = dst_mac
            output = in_port

            Send_Arp(ofsw, arp.ARP_REPLY,dst_mac, src_mac, dst_ip, src_ip, arp_target_mac, in_port, output)

#            log_msg = '[ARP REQUEST] from [IP %s : MAC %s] to [port %s : IP %s]'
#            logging.info(log_msg, srcip, src_mac, in_port, dstip, extra=ofsw.sw_id)

            retcode = "REQ"

        elif header_list[ARP].opcode == arp.ARP_REPLY:

            src_mac = header_list[ARP].src_mac
            dst_mac = header_list[ARP].dst_mac

            log_msg = '[ARP REPLY from CLIENT] IP %s : MAC %s PORT %s'
            logging.info(log_msg, srcip, src_mac, in_port, extra=ofsw.sw_id)

            arp_pkt_set.update({"SRC_IP": srcip})
            arp_pkt_set.update({"DST_IP": dstip})
            arp_pkt_set.update({"SRC_MAC": src_mac})
            arp_pkt_set.update({"DST_MAC": dst_mac})


            retcode = "REP"

    return retcode, arp_pkt_set


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
            logging.info("  [ SET ARP Packet In]  IP: %s PORT: %s", arp_key, arp_port)
            ofsw.flow_ctl.set_flow(flow_entry, 0)
        else:
            logging.info("  [ DELETE ARP Packet In]  IP: %s PORT: %s", arp_key, arp_port)
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
