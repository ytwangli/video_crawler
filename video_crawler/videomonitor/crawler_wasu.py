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
import time
import simplejson

site = 'wasu'
client_headers = { 'User-Agent': 'wasuClient',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-cn',
            'Cookie': 'SERVERID=af35e74984b4615fbd7d6d64b7e37053|1445592553|1445592510'
            }
headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.2; GT-I9505 Build/JDQ39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
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
    cur.executemany(u'insert into '+table+'(id,sid,duration,imageurl,title,online_time,play_times,video_num,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)


def get_wasu_duration_json(id_str):
    duration = 0
    url = 'http://www.wasu.cn/Api/getPlayInfoById/id/'+id_str+'/datatype/json'
    content = HTMLResource(url, headers).get_resource()
    if content is None:
        content = HTMLResource(url, headers).get_resource()
    index = content.find("<duration>") + len("<duration>")
    if index > 10:
        duration = int(content[index: content.find("</duration>", index)])
        if duration == 0:
            duration = 1
    else:
        print url
    return duration

def get_wasu_duration(_id):
    duration = 0
    status = 0
    base_url = 'http://www.wasu.cn/wap/Play/show/id/%s'
    try:
        content = HTMLResource(base_url % _id, headers).get_resource()
        if content is None:
            content = HTMLResource(base_url % _id, headers).get_resource()
        if content is not None:
            index = content.find("'duration' : '") + len("'duration' : '")
            if index > 50:
                duration = int(content[index: content.find("'", index)])
                if duration == 0:
                    duration = 1
            # video not exist
            elif 'var _gsChannel = "/wap/首页";' in content:
                duration = get_wasu_duration_json(str(_id))
                status = -100
            # video is vip
            else:
                duration = get_wasu_duration_json(str(_id))
                status = -101
    except Exception as e:
        print e
        traceback.print_exc()
        print _id
    return duration, status


def get_wasu_data(para):
    # http://clientapi.wasu.cn/Phone/vodinfo/id/6641911
    # http://clientapi.wasu.cn/Phone/rdjjinfo/id/6700150
    base_url = 'http://clientapi.wasu.cn/Phone/vodinfo/id/%s'
    _id, data_list, data_list_long = para
    try:
        content = JsonResource(base_url % _id, client_headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, client_headers).get_resource()
        if content is not None and 'name' in content:
            data = content
            # "wap_url": "www.wasu.cn\/wap\/Play\/show\/id\/6647735",
            sid = None
            imageurl = data['pic']
            # no duration
            video_num = 0
            dramadatas = data['dramadatas']
            if dramadatas is not None and dramadatas is not False:
                video_num = len(dramadatas)
            online_time = time.localtime(int(data['updatetime']))
            online_time = time.strftime('%Y-%m-%d %H:%M:%S', online_time)
            play_times = int(data['hits'])
            title = str(data['name']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            duration, status = get_wasu_duration(_id)
            if duration < 1500:
                data_list.append([_id,sid,duration,imageurl,title,online_time,play_times,video_num,status])
            else:
                data_list_long.append([_id,sid,duration,imageurl,title,online_time,play_times,video_num,status])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def craw_wasu(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 8
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_wasu_data, para_list)
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

# http://www.wasu.cn/wap/Play/show/id/4364488
# http://www.wasu.cn/Vip/tryed/id/4361731
# http://www.wasu.cn/Api/getPlayInfoById/id/4361731/datatype/xml
# http://www.wasu.cn/Api/getPlayInfoById/id/4001392/datatype/json
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    max_id = get_maxid(site)
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 1000
    while(True):
        count, count_long = craw_wasu(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)