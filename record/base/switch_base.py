
import logging

# -------------------------------                                                                                  
#                                                                                                                  
# App Base Import                                                                                 
#                        
# -------------------------------                                                                                  

from ryu.controller import dpset
from ryu.lib import dpid as dpid_lib

from base.flowctl_base import FlowCtl
from base.ofuro_data_base import OfuroData

class Ofsw(dict):
    def __init__(self, dp, logger):
        super(Ofsw, self).__init__()
        self.dpset    =  dp
        self.dpid_str =  dpid_lib.dpid_to_str(dp.id)
        self.sw_id    =  {'sw_id': self.dpid_str}
        self.logger   =  logger
        
        self.port_data =  PortData(self.dpset.ports)
        self.ofuro_data  =  OfuroData(self.dpset)

        self.flow_ctl  =  FlowCtl(self.dpset)

        self.client = {}

class PortData(dict):
    def __init__(self, ports):
        super(PortData, self).__init__()
        for port in ports.values():
            data = Port(port.port_no, port.hw_addr)
            self[port.port_no] = data


class Port(object):
    def __init__(self, port_no, hw_addr):
        super(Port, self).__init__()
        self.port_no = port_no
        self.mac = hw_addr

