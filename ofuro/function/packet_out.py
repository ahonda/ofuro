import logging

from lib.proto.pkt_proto import *
from ryu.ofproto         import ofproto_v1_3

def Send_Packet_Out(ofsw, in_port, output, data, data_str=None):
    actions = [ofsw.dpset.ofproto_parser.OFPActionOutput(output, 0)]
    ofsw.dpset.send_packet_out(buffer_id=UINT32_MAX, in_port=in_port,
                            actions=actions, data=data)
