import logging
import socket
import ConfigParser
import json

# For REST API

from ryu.app import wsgi
from ryu.app.wsgi import ControllerBase, WSGIApplication

# -------------------------------                                                                     
#                                                                                      
# App Base Import                                                                                 
#                        
# -------------------------------    
                                                    
from ryu.base import app_manager
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.exception import OFPUnknownVersion

from ryu.lib import dpid as dpid_lib
from ryu.lib import ofctl_v1_3
# -------------------------------

from base.switch_base import Ofsw
from base.flowctl_base import FlowCtl

from controller.rest_controller import RestAPIController


# -------------------------------
#
# Event Set using among instans 
#
# -------------------------------                                                                                  

#from lib.ipc.cast.switch import AddSwitchEvent
#from lib.ipc.cast.switch import LeaveSwitchEvent

ofuro_instance_name = 'ofuro_app'


# OFURO = OpenFlow Unity Rule  Operation

class OFURO_APP(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'wsgi': WSGIApplication
    }

    _LOGGER = None
    _OFSW_LIST={}

    def __init__(self, *args, **kwargs):
        super(OFURO_APP, self).__init__(*args, **kwargs)

        # logger configure
        self.set_logger(self.logger)
        self.ofuro_data = OFURO_APP_Data()

        self.waiters = {}

        context = {
            ofuro_instance_name : self,
            'waiters': self.waiters,
        }

        wsgi = kwargs['wsgi']
        wsgi.register(RestAPIController, context)

    @classmethod
    def set_logger(cls, logger):
        cls._LOGGER = logger
        cls._LOGGER.propagate = False
        hdlr = logging.StreamHandler()
        fmt_str = '[%(levelname)s:dpid=%(sw_id)s] %(message)s'
        hdlr.setFormatter(logging.Formatter(fmt_str))
        cls._LOGGER.addHandler(hdlr)


    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def datapath_handler(self, ev):
        if ev.enter:
            self.register_ofsw(ev.dp)

        else:
            self.unregister_ofsw(ev.dp)


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
 
        if dp.id not in self.waiters:
            return
 
        if msg.xid not in self.waiters[dp.id]:
            return
 
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)
 
        flags = dp.ofproto.OFPMPF_REPLY_MORE
 
        if msg.flags & flags:
            return
        del self.waiters[dp.id][msg.xid]
        lock.set()


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        dp_id = ev.msg.datapath.id
        if dp_id in self._OFSW_LIST:
            ofsw = self._OFSW_LIST[dp_id]
            ofsw.pkt_ctl.packet_in_handler(ev.msg)


    def register_ofsw(self, dp):
        dpid = {'sw_id': dpid_lib.dpid_to_str(dp.id)}

        default_ofuro_set = { "ARP": {}}

        if dpid["sw_id"] in self.ofuro_data:
            default_ofuro_set = self.ofuro_data[dpid["sw_id"]]

        try:
            ofsw = Ofsw(dp, default_ofuro_set, self._LOGGER)
        except OFPUnknownVersion as message:
            self._LOGGER.error(str(message), extra=dpid)
            return

        self._OFSW_LIST.setdefault(dp.id, ofsw)

        self._LOGGER.info('[OFSW] Join as OPSW Now !!', extra=dpid)

        for port in ofsw.port_data:
            self.logger.info('       [PORT NO] %s [MAC ADDRESS] %s',
                         ofsw.port_data[port].port_no, ofsw.port_data[port].mac, extra=ofsw.sw_id)

        ofsw.flow_ctl.arp_packet_in_flow(arp_data={}, flag=0)

 
    def unregister_ofsw(self, dp):
        if dp.id in self._OFSW_LIST:
            del self._OFSW_LIST[dp.id]

            dpid = {'sw_id': dpid_lib.dpid_to_str(dp.id)}
            self._LOGGER.info('[OFSW] Leave OpenFlow SW !!', extra=dpid)


def OFURO_APP_Data():
        f = open('ofuro.json','r')
        Ofuro_Data = json.load(f)
        f.close()
        return Ofuro_Data
