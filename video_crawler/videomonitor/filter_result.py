#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/opt/video_data/')
from resource.http import HTMLResource,JsonResource
from resource.database import DataBase

headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
            }
host = 2
def close_conn(conn, cur):
    cur.close()
    conn.close()

def get_result(table):
    data_list = []
    other_id_set = set()
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT iqiyi_tvid, other_dir, other_tvid, sim_N, iqiyi_title, other_title FROM '+table + ' WHERE host='+str(host)+' and status =1 order by id desc') # and create_date>"2015-09-25 10:00:00"
    # cur.execute('SELECT iqiyitvid, tudoudir, tudoutvid, sim_N, iqiyititle, tudoutitle FROM '+table + ' WHERE status =1 and sim_N >=3 ')
    count = 0
    for data in cur.fetchall():
        if data[2] not in other_id_set:
            count += 1
            # if '奇葩' in data[4]:
            #     count += 1
            other_id_set.add(data[2])
            data_list.append(data)
    DataBase.close_conn(conn, cur)
    print count
    return data_list

def get_info(table, id_str):
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT sid, duration, imageurl FROM '+table + ' WHERE id = '+id_str)
    for data in cur.fetchall():
        sid, duration, imageurl = data
    DataBase.close_conn(conn, cur)
    return sid, duration, imageurl


def get_result1(table,data_list):
    data_list1 = []
    tudou_id_set = set()
    conn, cur = DataBase.open_conn_video()
    for data in data_list:
        cur.execute('SELECT sim_N FROM '+table + ' WHERE host='+str(host)+' and status =1 and other_tvid = '+data[2])
        sum = 0
        for num in cur.fetchall():
            sum += num[0]
        if sum>=3:
            data_list1.append(data)
            print sum
            print '%s, %s' % (data[2], data[5])
        # elif sum>1:
            # print sum
            # print '%s, %s' % (data[2], data[5])

        # print sum

    DataBase.close_conn(conn, cur)
    return data_list1

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    data_list = get_result('report_data_new')
    data_list1 = get_result1('report_data_new',data_list)
    for data in data_list1:
        if host == 1:
            sid, duration, imageurl = get_info('tudou_long', str(data[2]))
            url = 'http://www.tudou.com/programs/view/' + sid + '/'
        else:
            sid, duration, imageurl = get_info('youku_long', str(data[2]))
            url = 'http://v.youku.com/v_show/id_'+sid+'.html'
        is_ok = 0
        content = HTMLResource(url, headers=headers).get_resource()
        if content is not None:
            is_ok = 1
            # soup = BeautifulSoup(content)
            # content1 = JsonResource('http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s' % data[2], headers=headers).get_resource()
            # for key in content1.keys():
            #     for datax in content1[key]:
            #         video_url = 'http://vr.tudou.com/v2proxy/v?sid=95001&id=%s&st=%s' % (datax['k'], key)
            #         # print video_url
        # print '%s,%s, %s, %s, %s, %s, %s, %s' % (data[2], url, data[5], duration, imageurl, data[0], data[4], is_ok)
        print '%s,%s,%s,%s' % (data[2], data[5], url, is_ok)

        # content = JsonResource('http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s' % data[2], headers=headers).get_resource()
        # for key in content.keys():
        #     for data in content[key]:
        #         video_url = 'http://vr.tudou.com/v2proxy/v?sid=95001&id=%s&st=%s' % (data['k'], key)
        #         print video_url


# http://www.tudou.com/outplay/goto/getItemSegs.action?iid=235599196
# http://vr.tudou.com/v2proxy/v?sid=95001&id=330988851&st=52
# http://vr.tudou.com/v2proxy/v?sid=95001&id=330988847&st=2
# http://ct.v2.tudou.com/f?id=330988847