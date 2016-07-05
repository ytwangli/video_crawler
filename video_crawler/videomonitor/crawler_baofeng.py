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

site = 'baofeng'
headers = { 'User-Agent': '暴风影音 3.2.1 rv:3.2.1.2 (iPhone; iPhone OS 9.0.2; zh_CN)',
            'Accept-Encoding': 'gzip',
            # 'Cookie': 'uid=fc33778a3ac4f1d74093c1963f1986b3563d56b6'
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
        if max_id_long < max_id:
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
    cur.executemany(u'insert into '+table+'(id,sid,duration,imageurl,title,online_time,play_times,video_num,info_site,comments,favorites,danmus,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)


def get_baofeng_data(para):
    # http://iphone.shouji.baofeng.com/iphone/album/976/10535976.json?mtype=normal&ver=3.2.1&g=23&td=0
    # http://iphone.shouji.baofeng.com/iphone/minfo/*/976/10535976_1.json?mtype=normal&ver=3.2.1&type=1&g=23&td=0&s=390929c1057ba4e6c3231c09d43505b126643a27
    # http://storm.baofeng.net/?c=storm://13100002078207%7C%7Cpid=wireless%7C%7Cchannel=
    base_url = 'http://iphone.shouji.baofeng.com/iphone/album/%s/%s.json?mtype=normal&ver=3.2.1&g=23&td=0'
    _id, data_list, data_list_long = para
    subid = _id % 1000
    try:
        content = JsonResource(base_url % (subid, _id), headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None and content['status'] == 1:
            data = content

            # http://www.baofeng.com/play/16/play-789516.html
            sid = None
            imageurl = data['info_img']
            duration = int(data['duration'])
            video_num = int(data['info_last_seq'])
            info_site = ','.join(data['info_sites'])
            online_time = data['info_update_at']
            comments = data['info_comment']
            if comments == '':
                comments = 0
            favorites = data['info_subscibe']
            danmus = data['info_danmaku']
            play_times = data['info_clicks']
            title = str(data['info_name']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            if duration < 1500:
                data_list.append([_id,sid,duration,imageurl,title,online_time,play_times,video_num,info_site,comments,favorites,danmus,0])
            else:
                data_list_long.append([_id,sid,duration,imageurl,title,online_time,play_times,video_num,info_site,comments,favorites,danmus,0])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def craw_baofeng(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 8
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_baofeng_data, para_list)
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
    # max_id = 8000000
    max_id = get_maxid(site)
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 1000
    while(True):
        count, count_long = craw_baofeng(start, start+step)
        # if count == 0:
        #     break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)