
import logging
from lib.proto.pkt_proto import *

# -------------------------------                                                                                  
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------                                                                                  
from ryu.controller import dpset
from ryu.lib import dpid as dpid_lib

class PktCtl(object):
    def __init__(self, dp, port, logger):
        self.dpset = dp
        self.port_data = port
        self.dpid_str = dpid_lib.dpid_to_str(dp.id)
        self.sw_id = {'sw_id': self.dpid_str}
        self.logger = logger


    def packet_in_handler(self, msg):

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        # TODO: Packet library convert to string
        # self.logger.debug('Packet in = %s', str(pkt), self.sw_id)
        header_list = dict((p.protocol_name, p)
                        for p in pkt.protocols if type(p) != str)

        if ARP in header_list:
            self.logger.info('[APR]  <in port>%s <keys> %s',
                             in_port, header_list, extra=self.sw_id)
            self._arp_reply(msg, header_list)
            return

        if ICMP in header_list:
            self.logger.info('[ICMP]  <in port>%s <keys> %s',
                             in_port, header_list, extra=self.sw_id)
            # Function to ICMP PACKET IN
            return

        if UDP in header_list:
            
            self.logger.info('[UDP]  <in port>%s <keys> %s',
                        in_port, header_list.values(), extra=self.sw_id)
            return

        if TCP in header_list:
            self.logger.info('[TCP]  <in port>%s <keys> %s',
                        in_port, header_list.keys(), extra=self.sw_id)
            return


    def _arp_reply(self, msg, header_list):

        # ARP packet handling.
        in_port = msg.match['in_port']
        src_ip = header_list[ARP].src_ip
        dst_ip = header_list[ARP].dst_ip
        srcip = ip_addr_ntoa(src_ip)
        dstip = ip_addr_ntoa(dst_ip)
   
        self.logger.info('[ARP]  <in port>%s <src IP>%s <dst IP>%s',
                        in_port, srcip, dstip, extra=self.sw_id)

        if src_ip == dst_ip:
        # GARP -> packet forward (normal)
            output = self.ofctl.dp.ofproto.OFPP_NORMAL
            self.ofctl.send_packet_out(in_port, output, msg.data)
            self.logger.info('Receive GARP from [%s].', srcip,
                             extra=self.sw_id)
            self.logger.info('Send GARP (normal).', extra=self.sw_id)

        else:
            if header_list[ARP].opcode == arp.ARP_REQUEST:
                # ARP request to router port -> send ARP reply
                src_mac = header_list[ARP].src_mac
                dst_mac = self.port_data[in_port].mac
                arp_target_mac = dst_mac
                output = in_port
                in_port = self.dpset.ofproto.OFPP_CONTROLLER

                self.send_arp(arp.ARP_REPLY, 
                              dst_mac, src_mac, dst_ip, src_ip,
                              arp_target_mac, in_port, output)

                log_msg = '2_Receive ARP request from [%s] to router port [%s].'
                self.logger.info(log_msg, srcip, dstip, extra=self.sw_id)
                self.logger.info('Send ARP reply to [%s]', srcip,
                                 extra=self.sw_id)

            elif header_list[ARP].opcode == arp.ARP_REPLY:
                #  ARP reply to router port -> suspend packets forward
                log_msg = '3_Receive ARP reply from [%s] to router port [%s].'
                self.logger.info(log_msg, srcip, dstip, extra=self.sw_id)

                packet_list = self.packet_buffer.get_data(src_ip)
                if packet_list:
                    # stop ARP reply wait thread.
                    for suspend_packet in packet_list:
                        self.packet_buffer.delete(pkt=suspend_packet)

                        # send suspend packet.
                        output = self.ofctl.dp.ofproto.OFPP_TABLE
                        for suspend_packet in packet_list:
                            self.ofctl.send_packet_out(suspend_packet.in_port,
                                                       output,
                                                       suspend_packet.data)
                            self.logger.info('Send suspend packet to [%s].',
                                             srcip, extra=self.sw_id)


    def send_arp(self, arp_opcode, src_mac, dst_mac,
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
        self.send_packet_out(in_port, output, pkt.data, data_str=str(pkt))


    def send_packet_out(self, in_port, output, data, data_str=None):
        actions = [self.dpset.ofproto_parser.OFPActionOutput(output, 0)]
        self.dpset.send_packet_out(buffer_id=UINT32_MAX, in_port=in_port,
                                actions=actions, data=data)

        # TODO: Packet library convert to string
        # if data_str is None:
        #     data_str = str(packet.Packet(data))
        # self.logger.debug('Packet out = %s', data_str, extra=self.sw_id)


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
