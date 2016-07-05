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

site = 'pptv'
headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; MI 4LTE Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36 V1_AND_SQ_5.9.1_272_YYB_D QQ/5.9.1.2535 NetType/WIFI WebP/0.3.2 Pixel/1080',
            'Accept': '*/*',
            'Referer': 'http://player.aplus.pptv.com/corporate/proxy/proxy.html',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8',
            # 'Cookie': 'sctx=; PUID=68bcf4237f9847f6bd27a2ac9a982a2a; PUID_CTM=315532800; ppi=302c31; ad_show=1',
            'X-Requested-With': 'com.tencent.mobileqq',
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

def get_pptv_data(para):
    # base_url = 'http://epg.api.pptv.com/detail.api?auth=d410fafad87e7bbf6c6dd62434345818&canal=18&userLevel=0&ppi=AQACAAAAAQAATkoAAAABAAAAAFYb2QAwLQIUZozYqBZXlBVxHpJVldyRl2OTuocCFQCIxNn5rPJ1pNb2cPTIvXEYer727w&appid=com.pplive.androidphone&appver=5.2.2&appplt=aph&vid=%s&series=1&virtual=1&ver=2&platform=android3&contentType=Preview'
    base_url = 'http://web-play.pptv.com/webplay3-0-%s.xml?version=4&type=mpptv&kk=c312abb400f993d82dbb9489f21846c6-6506-561b7382&fwc=0&complete=1&o=m.pptv.com&rcc_id=m.pptv.com&cb=getPlayEncode'
    _id, data_list, data_list_long = para
    try:
        content = JsonResource(base_url % _id, headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None:
            datas = content.get('childNodes', [])
            for data in datas:
                if data["tagName"] == "error":
                    break
                if data["tagName"] == "channel":
                    # http://v.pptv.com/show/NYFJxia6UBEKlI4s.html
                    sid = data['lk'][23: -5]
                    # http://v.img.pplive.cn/cp120/44/1b/441b029781a73aff2a12850daa32e341/31.jpg
                    # http://s1.pplive.cn/v/cap/id/w300.jpg
                    # http://s1.pplive.cn/v/cap/23557685/w640.jpg?v01
                    imageurl = data['pic']
                    duration = data['dur']
                    online_time = str(data['timestamp'])
                    title = str(data['nm']).replace('\r','|').replace('\n','|')  #.replace(',',';')
                    if duration < 1500:
                        data_list.append([_id,sid,duration,imageurl,title,online_time,0])
                    else:
                        data_list_long.append([_id,sid,duration,imageurl,title,online_time,0])
                    break
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def craw_pptv(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 8
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_pptv_data, para_list)
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
    # max_id = 23500000
    max_id = get_maxid(site)
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 500
    while(True):
        count, count_long = craw_pptv(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)