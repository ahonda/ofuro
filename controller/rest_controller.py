
import logging

# For REST API
import json
from webob import Response
from ryu.app import wsgi
from ryu.app.wsgi import ControllerBase
from ryu.lib import dpid as dpid_lib
from ryu.lib import ofctl_v1_3

from function.nat import Nat_Ready, Nat_Flow_Del
from function.arp import Arp_Flow

ofuro_instance_name = 'ofuro_app'

class RestAPIController(ControllerBase):

    _LOGGER = None

    def __init__(self, req, link, data, **config):
        super(RestAPIController, self).__init__(req, link, data, **config)

        self.ofuro_spp = data[ofuro_instance_name]
        self.waiters = data['waiters']

        self.headers = {
            'Content-Type': 'application/json'
        }


    @classmethod
    def set_logger(cls, logger):
        cls._LOGGER = logger
        cls._LOGGER.propagate = False
        hdlr = logging.StreamHandler()
        fmt_str = '[%(levelname)s:dpid=%(sw_id)s] %(message)s'
        hdlr.setFormatter(logging.Formatter(fmt_str))
        cls._LOGGER.addHandler(hdlr)


##############################################################
##################  GET method REST API ######################
##############################################################

    @wsgi.route('flow_entry', '/flow/{dpid}', methods=['GET'])
    def _get_flow_entry(self, req, dpid, **kwargs):
        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)

        datapath = ofsw.dpset

        flow_entry = ofctl_v1_3.get_flow_stats(datapath, self.waiters, {})
        content_body = json.dumps(flow_entry, indent=4)
        return wsgi.Response(status=200, body=content_body, headers=self.headers)


    @wsgi.route('arp_address', '/arp/{dpid}', methods=['GET'])
    def _get_arp_address(self, req, dpid, **kwargs):

        try:
            arp_addrs = self.ofuro_spp.ofuro_data[dpid]["ARP"].keys()
            content_body = json.dumps(arp_addrs, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)
        except:
            return wsgi.Response(status=400)


    @wsgi.route('ofuro_data', '/ofuro/{dpid}', methods=['GET'])
    def _get_ofuro_set(self, req, dpid, **kwargs):

        try:
            now_set = self.ofuro_spp.ofuro_data[dpid]
            content_body = json.dumps(now_set, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)
        except:
            now_set = self.ofuro_spp.ofuro_data
            content_body = json.dumps(now_set, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)



##############################################################
#################### ARP ADD/DELETE API ######################
##############################################################

#
#  curl -X PUT -d '{"addr":"10.0.1.1","mask":"255.255.255.0"}' http://127.0.0.1:8080/arp/0000000000000001 
#

    @wsgi.route('arp_add', '/arp/{dpid}', methods=['PUT'])
    def _put_arp_data(self, req, dpid, **kwargs):
        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)
        

        new_entry =eval(req.body)
        entry_addr = new_entry["addr"]
        entry_port = new_entry["port"]

        arp_data_set = {entry_addr : entry_port}

        try:
            Arp_Flow(ofsw, arp_data_set, flag=1)
            content_body = json.dumps(self.ofuro_spp.ofuro_data[dpid]["ARP"].keys(), indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

        except:
             logging.info('[** ARP ADD REQUEST ] No data')                                         
             return wsgi.Response(status=400)



    @wsgi.route('arp_delete', '/arp/{dpid}', methods=['DELETE'])
    def _delete_arp_data(self, req, dpid, **kwargs):

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)


        new_entry =eval(req.body)
        entry_addr = new_entry["addr"]
        entry_mask = new_entry["mask"]
        entry_port = new_entry["port"]

        arp_data_set = {entry_addr : {"MASK":entry_mask, "PORT":entry_port}}

        try:
            ofsw.flow_ctl.arp_packet_in_flow(arp_data_set, flag=2)
            content_body = json.dumps(self.ofuro_spp.ofuro_data[dpid]["ARP"].keys(), indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)
            
        except:
            logging.info('[** ARP DELETE REQUEST ] No data')
            return wsgi.Response(status=400)


#####################################
#  NAT Rule POST REQUEST
#
#  curl -X POST -d '{"a_ip":"192.168.x.x", "z_ip":"192.168.y.y" http://127.0.0.1:8080/nat/0000000000000001
####################################      


    @wsgi.route('nat_add', '/nat/{dpid}', methods=['POST'])
    def _add_nat_flow(self, req, dpid, **kwargs):

        logging.info('[REST_API : NAT ENTRY ADD]  Calling')                                         

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('[** NAT ADD REQUEST : ERROR] OFSW Not Found')
            return wsgi.Response(status=400)


        new_nat_entry =eval(req.body)
        ret = self.check_entry(ofsw, new_nat_entry)
        if ret != "":
            logging.info('[** NAT ADD REQUEST : ERROR] Same Entry Found :SW_IP %s', ret)                                         
            return wsgi.Response(status=400)

        try:
            Nat_Ready(ofsw, new_nat_entry)
            flow_entry = ofctl_v1_3.get_flow_stats(ofsw.dpset, self.waiters, {})

            content_body = json.dumps(flow_entry, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

        except:
            logging.info('[** NAT ADD REQUEST : ERROR] ENTRY Can not set')                                         
            return wsgi.Response(status=400)



    @wsgi.route('nat_del', '/nat/{dpid}', methods=['DELETE'])
    def _del_nat_flow(self, req, dpid, **kwargs):

        logging.info('[REST_API : NAT ENTRY DELETE]  Calling')                                         

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)

        del_nat_entry =eval(req.body)

        try:
            Nat_Flow_Del(ofsw, del_nat_entry)
            flow_entry = ofctl_v1_3.get_flow_stats(ofsw.dpset, self.waiters, {})

            content_body = json.dumps(flow_entry, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

        except:
             logging.info('[** FLOW ADD REQUEST ] bad data')                                         
             return wsgi.Response(status=400)


    def check_entry(self, ofsw, new_entry_set):

        chk_port = []
        chk_swip = []
        chk_clip = []

        for new_entry in new_entry_set:
            chk_port.append(new_entry["SW_PORT"])
            chk_swip.append(new_entry["SW_IP"])
            chk_clip.append(new_entry["CLIENT_IP"])

        for entry_index, nat_entry in enumerate(ofsw.ofuro_data.nat_entry):
            for nat_data in nat_entry:
                if nat_data["SW_IP"] in chk_swip:
                    logging.info("------> %s", nat_data["SW_IP"])
                    return nat_data["SW_IP"]

        return ""
