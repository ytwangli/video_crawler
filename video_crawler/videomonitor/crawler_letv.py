#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/opt/video_data/')
from resource.http import HTMLResource,JsonResource
from resource.database import DataBase
import threadpool
import datetime
import time
import traceback

site = 'letv'
headers = { 'User-agent': 'LetvGphoneClient/5.9.6 Mozilla/5.0 (Linux; Android 4.4.4; MI 3W Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36',
            'SSOTK': '',
            'Accept-Encoding': 'gzip',
            }

# GET /play?tm=1443403752&playid=0&tss=ios&pcode=010110106&version=5.9.6&cid=1&pid=10008768&vid=22932318&devid=e5383f3bb33258022a45e3d56573fff1 HTTP/1.1
# SSOTK:
# User-agent:
# Host: api.mob.app.letv.com
# Connection: Keep-Alive
# Accept-Encoding: gzip

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


def save(table, result):
    conn, cur = DataBase.open_conn_video()
    cur.executemany(u'insert into '+table+'(id,duration,imageurl,title,date,status) values(%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)

# http://www.letv.com/ptv/vplay/23613703.html
def get_letv_data(para):
    # url = 'http://api.mob.app.letv.com/play?tm=1443403752&playid=0&tss=ios&pcode=010110106&version=5.9.6&cid=1&pid=10008768&vid=22932318&devid=e5383f3bb33258022a45e3d56573fff1 HTTP/1.1
    base_url = 'http://api.mob.app.letv.com/play?tm=%s&playid=0&tss=ios&pcode=010110041&version=5.9.6&cid=1&pid=10008768&vid=%s&devid=e5383f3bb33258022a45e3d56573fff1'
    _id, tm, data_list, data_list_long = para
    try:
        url = base_url % (tm, _id)
        content = JsonResource(url, headers).get_resource()
        if content is None:
            content = JsonResource(url, headers).get_resource()
        if content is not None and content['header']['status'] == '1':
            data = content.get('body', {}).get('videoInfo', None)
            if data is not None:
                imageurl = data['picAll']['320*200']
                duration = data['duration']
                duration = int(duration)
                # 标题中需要去掉换行
                title = data['nameCn'].replace('\r','|').replace('\n','|')  #.replace(',',';')
                # 2012-01-01 00:00:00
                date_str = data['releaseDate']
                if duration < 1500:
                    data_list.append([_id,duration,imageurl,title,date_str,0])
                else:
                    data_list_long.append([_id,duration,imageurl,title,date_str,0])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id


def craw_letv(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    tm = int(time.time())
    while start < end:
        para_list.append([start, tm, data_list, data_list_long])
        start += 1

    pool_size = 1
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_letv_data, para_list)
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
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 500
    while(True):
        count, count_long = craw_letv(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)