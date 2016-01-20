import os
import logging
import pickle

def Write_Record(ofsw, e_type=0):

    if   e_type == 0:
        file_name = "nat.json"
        dump_data = ofsw.ofuro_data.nat_entry
    elif e_type == 1:
        file_name = "arp.json"
        dump_data = ofsw.ofuro_data.arp_entry        

    recdir = "./record/" + ofsw.dpid_str + "/"
    s_file = recdir + file_name

    if not os.path.isdir(recdir):
        os.makedirs(recdir)

    f = open(s_file, 'w')

    pickle.dump(dump_data, f)
    f.close()



def Read_Record(ofsw, e_type=0):

    if   e_type == 0:
        file_name = "nat.json"
    elif e_type == 1:
        file_name = "arp.json"

    recdir = "./record/" + ofsw.dpid_str + "/"
    s_file = recdir + file_name

    if not os.path.isdir(recdir):
        os.makedirs(recdir)

    f = open(s_file)

    dump_data = pickle.load(f)
    f.close()
    return dump_data
