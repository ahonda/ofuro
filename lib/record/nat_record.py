import os

def File_Write_Flow(dpid, entry, e_type=0):
    
    recdir = "./record/" + dpid + "/"
    s_file = recdir + "static_flow.json"

    if e_type == 0: e_type = "static"
    elif e_type == 1: e_type = "arp"

    ret_flag, line_num, ret_num, ret_entry = Check_File(dpid, entry)

    if ret_flag == -1:
        f = open(s_file, 'w')
    elif ret_flag == -2:
        print "Find Same Flow entry"
        return 
    else:
        f = open(s_file, 'a')

    ret_num += 1

    w =  str(ret_num) + "___" + e_type + "___" + str(entry) +"\n"

    f.write(w)
    f.close()


def File_Delete_Flow(dpid, entry, e_num=0):

    recdir = "./record/" + dpid + "/"
    s_file = recdir + "static_flow.json"
    tmp_file = recdir + "tmp_flow.json"

    ret_flag, line_num, end_num, ret_entry = Check_File(dpid, entry, e_num)

    if ret_flag == -2:
         f1 = open(s_file, 'r')
         f2 = open(tmp_file, 'w')
    else:
        return "{}"

    i = 0
    
    for line in f1:
        i += 1
        if i == line_num:
            continue

        f2.write(line)

    f1.close()
    f2.close()

    os.remove(s_file)
    os.rename(tmp_file, s_file)
    
    return ret_entry

def Check_File(dpid, entry, e_num=0)  :
    flag = 0
    line_num = 0
    num = 0
    rstr = ""

    recdir = "./record/" + dpid + "/"
    s_file = recdir + "static_flow.json"

    print recdir

    if not os.path.isdir(recdir):
        os.makedirs(recdir)

    try:
        now_lines = sum(1 for line in open(s_file))

    except:
        print "File Not Found!"
        flag = -1
        return [flag, line_num, num, rstr]

    else: 
        if now_lines == 0:
            flag = -1
            return [flag, line_num, num, rstr]
        else:
            flag = 1
            f = open(s_file, 'r')
            for get_line in f :
                line_num += 1
                a, b, c = get_line[:-1].split("___")
                c = eval(c)
                num = int(a)

                if entry == c or num == e_num:
                    flag = -2
                    break

            f.close()
            return [flag, line_num, num, c]

