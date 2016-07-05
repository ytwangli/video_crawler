#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/opt/video_data/')
from resource.http import HTMLResource,JsonResource
from resource.database import DataBase
import threadpool
import datetime
import traceback

site = 'hunantv'
headers = { 'User-Agent': 'imgo4Android/ Dalvik (Android 4.4.4)',
            'Accept-Encoding': 'gzip'
            }

def get_maxid(table):
    max_id = 0
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT max(id) FROM '+table)
    for data in cur.fetchall():
        max_id = data[0]
    cur.execute('SELECT max(id) FROM '+table+'_long')
    for data in cur.fetchall():
        max_id_long = data[0]
        if max_id_long > max_id:
            max_id = max_id_long
    DataBase.close_conn(conn, cur)
    return max_id

def get_datas():
    data_list = []
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT id,sid FROM '+site+' WHERE duration=0 order by id desc;')
    for data in cur.fetchall():
        data_list.append([data[0],data[1]])
    DataBase.close_conn(conn, cur)
    return data_list

def save(table, result):
    conn, cur = DataBase.open_conn_video()
    cur.executemany(u'insert into '+table+'(id,sid,duration,imageurl,title,online_time,status) values(%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)

def get_hunantv_data(para):
    # http://mobile.api.hunantv.com/v3/video/getVideoInfo?userId=&osVersion=4.4.4&device=MI+4LTE&appVersion=4.5.3&videoId=1801140&ticket=&channel=xiaomi&mac=i867080024277455&osType=android
    # http://mobile.api.hunantv.com/v4/video/getVideoInfo?userId=&osVersion=4.4.4&seqId=d3d61c4b551033d3a018f7333880e325&uid=&device=MI+3W&appVersion=4.6.3&videoId=2945963&ticket=&channel=xiaomi&mac=i864690026317050&osType=android
    base_url = 'http://mobile.api.hunantv.com/v4/video/getVideoInfo?userId=&osVersion=4.4.4&seqId=d3d61c4b551033d3a018f7333880e325&uid=&device=MI+3W&appVersion=4.6.3&videoId=%s&ticket=&channel=xiaomi&mac=i864690026317050&osType=android'
    _id, data_list, data_list_long = para
    try:
        content = JsonResource(base_url % _id, headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None and content['err_code'] == 200:
            data = content['data']
            # "pcUrl": "http://www.hunantv.com/v/1/150217/f/1721800.html",
            sid = data['pcUrl'][23: -5]
            imageurl = data['imageUrl']
            duration = data['time']
            online_time = data['publishTime']
            title = str(data['videoName']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            if duration < 1500:
                data_list.append([_id,sid,duration,imageurl,title,online_time,0])
            else:
                data_list_long.append([_id,sid,duration,imageurl,title,online_time,0])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def craw_hunantv(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 8
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_hunantv_data, para_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    pool.dismissWorkers(pool_size, do_join=True)

    count = len(data_list)
    if count > 0:
        save(site, data_list)
    count_long = len(data_list_long)
    if count_long > 0:
        save(site+'_long', data_list_long)
    print count, count_long
    return (count + count_long, count_long)


def save_oplog(site, id_start, num, num_long):
    id_end = get_maxid(site)
    print id_end
    exe_time = datetime.datetime.now()
    conn, cur = DataBase.open_conn_video()
    cur.execute('insert into oplog(site, id_start, id_end, num, num_long, create_date, update_date) values(%s, %s, %s, %s, %s, %s, %s)',( site, id_start, id_end, num, num_long, exe_time, exe_time))
    conn.commit()
    DataBase.close_conn(conn, cur)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    max_id = get_maxid(site)
    # max_id = 2945000
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 500
    while(True):
        count, count_long = craw_hunantv(start, start+step)
        # if count == 0:
        #     break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)