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

site = 'acfun'
headers = { 'User-Agent': 'AcFun/4.0.1 (iPhone; iOS 9.0.2; Scale/2.00)',
            'productId': '2000',
            'market': 'appstore',
            'appVersion': '4.0.1',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-Hans-CN;q=1',
            'deviceType': '0',
            'resolution': '640x1136',
            'udid': '6A76871F-7258-4304-8C7E-F0A0E02A6E27',
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

def updata_datas():
    data_list = []
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT id, sid, video_cid, video_from FROM acfun WHERE duration=0 and status=0 order by id asc')
    for data in cur.fetchall():
        data_list.append([data[0], data[1], data[2], data[3]])
    base_url = 'http://api.aixifan.com/videos/%s'
    for data in data_list:
        _id = data[0]
        try:
            content = JsonResource(base_url % _id, headers).get_resource()
            if content is None:
                content = JsonResource(base_url % _id, headers).get_resource()
            if content is not None:
                if content['code'] == 200:
                    for video in content['data']['videos']:
                        video_duration = int(video['time'])
                        video_cid = video['videoId']
                        video_from = video['sourceType']
                        if video_duration>0 and video_cid==data[2] and video_from==data[3]:
                            if video_duration < 1500:
                                cur.execute('update acfun set duration=%s where id=%s' % (video_duration, _id))
                                conn.commit()
                            else:
                                cur.execute('SELECT video_cid,sid,duration,imageurl,title,online_time,play_times,video_vid,video_url,video_num,video_title,video_from,type_id,favorites,danmus,comments,author,description,status FROM acfun WHERE id='+str(_id))
                                for data1 in cur.fetchall():
                                    tmp_data = [data1[0],data1[1],video_duration,data1[3],data1[4],data1[5],data1[6],data1[7],data1[8],data1[9],data1[10],data1[11],data1[12],data1[13],data1[14],data1[15],data1[16],data1[17],data1[18]]
                                    cur.executemany(u'insert into acfun_long(video_cid,sid,duration,imageurl,title,online_time,play_times,video_vid,video_url,video_num,video_title,video_from,type_id,favorites,danmus,comments,author,description,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', tmp_data)
                                    break
                                cur.execute('delete from acfun where id=%s' % _id)
                                conn.commit()
                else:
                    code = content['code']
                    cur.execute('update acfun set status=%s where id=%s' % (code, _id))
                    conn.commit()
        except Exception as e:
            print _id
            print e
            traceback.print_exc()
    DataBase.close_conn(conn, cur)

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
    cur.executemany(u'insert into '+table+'(video_cid,sid,duration,imageurl,title,online_time,play_times,video_vid,video_url,video_num,video_title,video_from,type_id,favorites,danmus,comments,author,description,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)

# http://api.aixifan.com/bangumis/1470255
# http://api.aixifan.com/bangumis/1470370
# 番剧集
def get_acfun_data(para):
    sid, data_list, data_list_long = para
    # http://api.aixifan.com/videos/2281025
    url = 'http://api.aixifan.com/videos/%s' % (sid)
    try:
        content = JsonResource(url, headers).get_resource()
        if content is None:
            content = JsonResource(url, headers).get_resource()
        if content is not None and content['code'] == 200:
            data = content['data']
            # http://www.acfun.tv/v/ac2280791
            type_id = data['channelId']
            imageurl = data['cover']
            play_times = int(data['visit']['views'])
            favorites = int(data['visit']['stows'])
            danmus = int(data['visit']['danmakuSize'])
            comments = int(data['visit']['comments'])
            author = data['owner']['name']
            video_nums = int(data['videoCount'])
            online_time = time.localtime(data['releaseDate']/1000)
            online_time = time.strftime('%Y-%m-%d %H:%M:%S', online_time)
            title = str(data['title']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            description = str(data['description']).replace('\r','|').replace('\n','|')  #.replace(',',';')
            is_save = False
            video_num = 0
            for video in data['videos']:
                video_num += 1
                video_cid = video['videoId']
                video_vid = video['sourceId']
                video_from = video['sourceType']
                video_title = video['title']
                video_url = video['url']
                video_duration = video['time']
                description_save = ''
                if not is_save:
                    description_save = description
                    is_save = True
                if video_duration < 1500:
                    data_list.append([video_cid,sid,video_duration,imageurl,title,online_time,play_times,video_vid,video_url,video_num,video_title,video_from,type_id,favorites,danmus,comments,author,description_save,0])
                else:
                    data_list_long.append([video_cid,sid,video_duration,imageurl,title,online_time,play_times,video_vid,video_url,video_num,video_title,video_from,type_id,favorites,danmus,comments,author,description_save,0])
    except Exception as e:
        print e
        traceback.print_exc()
        print sid

def craw_acfun(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 8
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_acfun_data, para_list)
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
    # get_acfun_data([2316108, [], []])
    # updata_datas()
    # max_id = 1900000
    max_id = get_maxid(site)
    start = max_id + 1
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 1000
    while(True):
        count, count_long = craw_acfun(start, start+step)
        # if count == 0:
        #     break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)