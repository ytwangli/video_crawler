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
import hashlib

site = 'bilibili'
headers = { 'User-Agent': 'Mozilla/5.0 BiliDroid/4.6.0 (bbcallen@gmail.com)',
            'Accept-Encoding': 'gzip',
            'X-Request-Config': 'response-cache-if-no-connection'
            }
video_headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36',
            'Accept-Language': ' zh-CN,zh;q=0.8',
            'TE': 'trailers'
            }

def get_maxid(table):
    max_id = 0
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT max(sid) FROM '+table)
    for data in cur.fetchall():
        max_id = data[0]
    cur.execute('SELECT max(sid) FROM '+table+'_long')
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
    cur.executemany(u'insert into '+table+'(video_cid,sid,duration,imageurl,title,online_time,play_times,video_vid,video_type,video_page,video_title,video_from,video_format,video_quality,type_name,favorites,danmus,comments,author,description,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)

def get_bilibili_video_data_android(para):
    aid, video_page, cid = para
    # http://interface.bilibili.com/playurl?platform=android&_device=android&_hwid=1988e937f2dfbab2&_aid=3086179&_tid=0&_p=2&_down=0&cid=4848559&quality=3&otype=json&appkey=452d3958f048c02a&type=mp4&sign=173c47bdcf6546af7654dc32f351e3cf
    url_para = 'platform=android&_device=android&_hwid=1988e937f2dfbab2&_aid=%s&_tid=0&_p=%s&_down=0&cid=%s&quality=3&otype=json&appkey=452d3958f048c02a&type=mp4' % (aid, video_page, cid)
    parakey = url_para + 'ea85624dfcf12d7cc7b2b3a94fac1f2c'
    sign = hashlib.md5(parakey.encode('utf-8')).hexdigest()
    url = 'https://interface.bilibili.com/playurl?%s&sign=%s' % (url_para, sign)
    try:
        content = JsonResource(url, video_headers).get_resource()
        if content is None:
            content = JsonResource(url, video_headers).get_resource()
        if content is not None and 'from' in content:
            data = content
            video_from = data['from']
            video_format = data.get('accept_format', data.get(video_from+'_vtype', ''))
            video_quality = '3'
            if 'accept_quality' in data:
                l = []
                for d in data['accept_quality']:
                    l.append(str(d))
                video_quality = ','.join(l)
            video_duration = data['timelength']/1000
            return [video_from, video_format, video_quality, video_duration]
        else:
            print para
            print content
    except Exception as e:
        print e
        traceback.print_exc()
        print para
    print url
    return None


def get_bilibili_video_data(para):
    aid, video_page, cid = para
    # http://interface.bilibili.com/playurl?appkey=95acd7f6cc3392f3&quality=4&otype=json&type=flv&cid=35175
    url = 'http://interface.bilibili.com/playurl?appkey=95acd7f6cc3392f3&quality=3&otype=json&type=flv&cid=%s' % (cid)
    try:
        content = JsonResource(url, video_headers).get_resource()
        if content is None:
            content = JsonResource(url, video_headers).get_resource()
        if content is not None and 'durl' in content:
            data = content
            durl = data['durl']
            if type(durl)==list:
                durl = durl[0]
            video_url = durl['url'].replace('http://', '')
            video_url = video_url[0: video_url.find('/')]
            video_from = data.get('from', video_url)
            video_format = data.get('accept_format', data.get(video_from+'_vtype', ''))
            video_quality = '3'
            if 'accept_quality' in data:
                l = []
                for d in data['accept_quality']:
                    l.append(str(d))
                video_quality = ','.join(l)
            video_duration = data.get('timelength', durl['length'])/1000
            return [video_from, video_format, video_quality, video_duration]
        elif content['result'] != 'error':
            print para
            print content
    except Exception as e:
        print e
        traceback.print_exc()
        print para
    print url
    return None

# http://app.bilibili.com/bangumi/season?_device=android&_hwid=1988e937f2dfbab2&appkey=c1b107428d337928&build=406001&platform=android&sp_id=56714&ts=1445501378000&type=sp&sign=2e7ca25cd7e8b6daecd47b5f85e8a14b
# 番剧集的每个子集都有个aid并对应一个video_cid，不需要单独爬
def get_bilibili_data(para):
    aid, data_list, data_list_long = para
    # https://api.bilibili.com/view?_device=android&_hwid=1988e937f2dfbab2&appkey=c1b107428d337928&batch=1&build=406001&check_area=1&id=3086179&platform=android&sign=ed0cd5ba7a8e16aad356a17f3acf9c04
    exe_time = datetime.datetime.now()
    url_para = '_device=android&_hwid=1988e937f2dfbab2&appkey=c1b107428d337928&batch=1&build=406001&check_area=1&id=%s&platform=android' % (aid)
    parakey = url_para + 'ea85624dfcf12d7cc7b2b3a94fac1f2c'
    sign = hashlib.md5(parakey.encode('utf-8')).hexdigest()
    url = 'https://api.bilibili.com/view?%s&sign=%s' % (url_para, sign)
    try:
        content = JsonResource(url, headers).get_resource()
        if content is None:
            content = JsonResource(url, headers).get_resource()
        if content is not None and 'list' in content:
            data = content
            # http://www.bilibili.com/video/av3054925/
            sid = None
            type_id = data['tid']
            type_name = data['typename']
            imageurl = data['pic']
            play_times = int(data['play'])
            favorites = int(data['favorites'])
            danmus = int(data['video_review'])
            comments = int(data['review'])
            author = data['author']
            video_nums = int(data['pages'])
            online_time = str(data['created_at']) # created
            title = str(data['title']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            description = str(data['description']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            is_save = False
            for k, video in data['list'].iteritems():
                video_cid = video['cid']
                video_vid = video['vid']  # vupload_4866228
                video_type = video['type']
                video_page = video['page']
                video_title = video['part']
                video_data = get_bilibili_video_data([aid, video_page, video_cid])
                if video_data is not None:
                    video_from, video_format, video_quality, video_duration = video_data
                    description_save = ''
                    if not is_save:
                        description_save = description
                        is_save = True
                    sid = aid
                    if video_duration < 1500:
                        data_list.append([video_cid,sid,video_duration,imageurl,title,online_time,play_times,video_vid,video_type,video_page,video_title,video_from,video_format,video_quality,type_name,favorites,danmus,comments,author,description_save,0])
                    else:
                        data_list_long.append([video_cid,sid,video_duration,imageurl,title,online_time,play_times,video_vid,video_type,video_page,video_title,video_from,video_format,video_quality,type_name,favorites,danmus,comments,author,description_save,0])
                else:
                    print aid
        else:
            code = content['code']
            # 404 已删除， 403 侵权下线
            if code != -404 and code != -403:
                print aid
                print content
    except Exception as e:
        print e
        traceback.print_exc()
        print aid

def craw_bilibili(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 1
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_bilibili_data, para_list)
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

# {'code': -503, 'result': [], 'error': 'overspeed'}
# http://static.hdslb.com/miniloader.swf?aid=21410&page=1
# https://static-s.bilibili.com/play.swf?aid=21410&page=1
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # max_id = 2380000
    max_id = get_maxid(site)
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 1000
    while(True):
        count, count_long = craw_bilibili(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)