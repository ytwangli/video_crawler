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

site = 'tudou'
headers = { 'User-Agent': 'Tudou;5.4;Android;4.4.4;MI 4LTE',
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
    cur.executemany(u'insert into '+table+'(id,sid,duration,imageurl,title,play_times,comments,tags,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)


def get_tudou_data(para):
    # http://api.3g.tudou.com/v4/play/detail?pid=d388af1027ad9100&_t_=1444721146&_e_=md5&_s_=6765860db4dd8e93698cad70f58277bc&guid=bc6136e9eadb1a1045110061ef6dc356&ver=5.4&network=WIFI&aid=235145&show_playlist=1
    # http://api.3g.tudou.com/v4/play/detail?pid=7b979ca489bcc36e&_t_=1435643508&_e_=md5&guid=4c49c456777e2bb7a2fc27d7260d96be&ver=4.0&network=WIFI&show_playlist=1&iid=249382884

    base_url = 'http://api.3g.tudou.com/v4/play/detail?pid=7b979ca489bcc36e&_t_=1435643508&_e_=md5&guid=4c49c456777e2bb7a2fc27d7260d96be&ver=4.0&network=WIFI&show_playlist=1&iid=%s'
    _id, data_list, data_list_long = para
    try:
        status = 0
        content = JsonResource(base_url % _id, headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None:
            data = content.get('detail', {})
            if 'iid' in data:
                imageurl = data['img_hd']
                if imageurl == '':
                    imageurl = data['img']
                sid = data['iid']
                duration = data['duration']
                duration = int(duration)
                # 标题中需要去掉换行
                title = data['title'].replace('\r','|').replace('\n','|')  #.replace(',',';')
                user_play_times = data['user_play_times']
                total_comment = data['total_comment']
                cats = data['cats']
                item_media_type = data.get('item_media_type', '')
                if item_media_type == '音频':
                    status = -1
                if duration < 1500:
                    data_list.append([_id,sid,duration,imageurl,title,user_play_times,total_comment,cats,status])
                else:
                    data_list_long.append([_id,sid,duration,imageurl,title,user_play_times,total_comment,cats,status])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id


def craw_tudou(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 12
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_tudou_data, para_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    pool.dismissWorkers(pool_size, do_join=True)

    count = len(data_list)
    if count > 0:
        print data_list[-1][0]
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
    step = 1000
    while(True):
        count, count_long = craw_tudou(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)