import os
import logging
import pickle

def Write_Record(ofsw, e_type=0):

    path, dump_data = check_record_file(ofsw, e_type)

    f = open(path, 'w')
    pickle.dump(dump_data, f)
    f.close()


def Read_Record(ofsw, e_type=0):

    path, dump_data = check_record_file(ofsw, e_type)

    f = open(path)
    dump_data = pickle.load(f)
    f.close()
    return dump_data

def check_record_file(ofsw, e_type):

    if   e_type == 0:
        file_name = "nat.json"
        dump_data = ofsw.ofuro_data.nat_entry
    elif e_type == 1:
        file_name = "arp.json"
        dump_data = ofsw.ofuro_data.arp_entry

    recdir = "./record/" + ofsw.dpid_str + "/"
    path = recdir + file_name


    ret = os.path.isdir(recdir)
    if ret == False:
        os.makedirs(recdir)

    ret = os.path.exists(path)

    if ret == False:
        f = open(path, "w")
        pickle.dump(dump_data,f)
        f.close()

    return path, dump_data
