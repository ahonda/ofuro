
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

    @wsgi.route('flow_entry', '/flow/{dpid}/', methods=['GET'])
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


    @wsgi.route('arp_address', '/arp/{dpid}/', methods=['GET'])
    def _get_arp_address(self, req, dpid, **kwargs):

        try:
            arp_addrs = self.ofuro_spp.ofuro_data[dpid]["ARP"].keys()
            content_body = json.dumps(arp_addrs, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)
        except:
            return wsgi.Response(status=400)


    @wsgi.route('ofuro_data', '/ofuro/{dpid}/', methods=['GET'])
    def _get_ofuro_set(self, req, dpid, **kwargs):

        try:
            now_set = self.ofuro_spp.ofuro_data[dpid]
            content_body = json.dumps(now_set, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)
        except:
            now_set = self.ofuro_spp.ofuro_data
            content_body = json.dumps(now_set, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)


#####################################
#  NAT Rule POST REQUEST
#
#  curl -X POST -d '{"a_ip":"192.168.x.x", "z_ip":"192.168.y.y" http://127.0.0.1:8080/nat/0000000000000001
####################################      

    @wsgi.route('nat_get_all', '/nat/{dpid}', methods=['GET'])
    def _get_nat_entry_all(self, req, dpid, **kwargs):

        logging.info('[REST_API : NAT ENTRY GET]  Calling')                                         

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)

        nat_entry = ofsw.ofuro_data.get_nat_entry()
        content_body = json.dumps(nat_entry, indent=4)

        if nat_entry == None:
            logging.info('<*** ERROR ***>  NAT ENTRY : %s ' , nat_entry) 
            return wsgi.Response(status=400, body=content_body, headers=self.headers)

        else:
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

#        nat_entry =  ofsw.ofuro_data.NatEntry
#        content_body = json.dumps(nat_entry, indent=4)
#        return wsgi.Response(status=200, body=content_body, headers=self.headers)



    @wsgi.route('nat_get', '/nat/{dpid}/{uuid}', methods=['GET'])
    def _get_nat_entry(self, req, dpid, uuid, **kwargs):

        logging.info('[REST_API : NAT ENTRY GET]  UUID: %s', uuid)                                         

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                   
            return wsgi.Response(status=400)

        nat_entry = ofsw.ofuro_data.get_nat_entry(uuid)
        content_body = json.dumps(nat_entry, indent=4)

        if nat_entry == None:
            logging.info('<*** ERROR ***>  NAT ENTRY : %s ' , nat_entry) 
            return wsgi.Response(status=400, body=content_body, headers=self.headers)

        else:
            return wsgi.Response(status=200, body=content_body, headers=self.headers)


    @wsgi.route('nat_add', '/nat/{dpid}', methods=['POST'])
    def _add_nat_entry(self, req, dpid, **kwargs):

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
            entry = Nat_Ready(ofsw, new_nat_entry)
            content_body = json.dumps(entry, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

        except:
            logging.info('[** NAT ADD REQUEST : ERROR] ENTRY Can not set')                                         
            return wsgi.Response(status=400)



    @wsgi.route('nat_del', '/nat/{dpid}/{uuid}', methods=['DELETE'])
    def _del_nat_entry(self, req, dpid, uuid, **kwargs):

        logging.info('[REST_API : NAT ENTRY DELETE]  Calling')                                         

        dp_id = dpid_lib.str_to_dpid(dpid)

        if dp_id in  self.ofuro_spp._OFSW_LIST.keys():
            ofsw = self.ofuro_spp._OFSW_LIST[dp_id]
        else:
            logging.info('<*** ERROR ***>  OFSW Not Found')                                         
            return wsgi.Response(status=400)

        try:
            ret = Nat_Flow_Del(ofsw, uuid)

            logging.info("RET FLAG : %s", ret)

            content_body = json.dumps(ofsw.ofuro_data.NatEntry, indent=4)
            return wsgi.Response(status=200, body=content_body, headers=self.headers)

        except:
             logging.info('[** FLOW DELETE REQUEST ] bad data')                                         
             return wsgi.Response(status=400)




    def check_entry(self, ofsw, new_entry_set):

        chk_port = []
        chk_swip = []
        chk_clip = []

        for new_entry in new_entry_set:
            chk_port.append(new_entry["SW_PORT"])
            chk_swip.append(new_entry["SW_IP"])
            chk_clip.append(new_entry["CLIENT_IP"])

        for entry_uuid, nat_entry in ofsw.ofuro_data.NatEntry.items():
            for nat_data in nat_entry["ENTRY"]:
                if nat_data["SW_IP"] in chk_swip:
                    logging.info("------> %s", nat_data["SW_IP"])
                    return nat_data["SW_IP"]

        return ""
