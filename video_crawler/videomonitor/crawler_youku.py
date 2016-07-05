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

site = 'youku'
headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
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

def updata_datas():
    data_list = []
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT id FROM youku_long WHERE status=0 order by id asc')
    for data in cur.fetchall():
        data_list.append(data[0])
    # https://openapi.youku.com/v2/videos/show_basic.json?video_id=XNjY1NDA2MDAw&client_id=b10ab8588528b1b1
    base_url = 'http://play.youku.com/play/get.json?vid=%s&ct=10'
    for _id in data_list:
        try:
            content = JsonResource(base_url % _id, headers).get_resource()
            if content is None:
                content = JsonResource(base_url % _id, headers).get_resource()
            if content is not None and content['e']['code']==0:
                if 'error' in content['data']:
                    code = content['data']['error']['code']
                    cur.execute('update youku_long set status=%s where id=%s' % (code, _id))
                    conn.commit()
        except Exception as e:
            print _id
            print e
            traceback.print_exc()
    DataBase.close_conn(conn, cur)


def get_datas(num=10000):
    data_list = []
    conn, cur = DataBase.open_conn_video()
    cur.execute('SELECT id FROM '+site+' WHERE duration=0 and status=0 order by id asc LIMIT ' + str(num))
    for data in cur.fetchall():
        data_list.append(data[0])
    DataBase.close_conn(conn, cur)
    return data_list

def save(table, result):
    conn, cur = DataBase.open_conn_video()
    cur.executemany(u'insert into '+table+'(id,sid,duration,imageurl,up,down,tags,title,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', result)
    conn.commit()
    DataBase.close_conn(conn, cur)

def update(table, result):
    conn, cur = DataBase.open_conn_video()
    for data in result:
        cur.execute('update %s set duration=%s,status=%s where id=%s' % (table, data[2], data[8], data[0]))
    conn.commit()
    DataBase.close_conn(conn, cur)

def delete(table, result):
    conn, cur = DataBase.open_conn_video()
    for data in result:
        cur.execute('delete from %s where id=%s' % (table, data[0]))
    conn.commit()
    DataBase.close_conn(conn, cur)

# User-Agent: Youku;5.2.1;iPhone OS;9.1;iPhone6,1
# http://api.mobile.youku.com/layout/ios5_0/play/detail?area_code=1&brand=apple&btype=iPhone6%2C1&deviceid=0f607264fc6318a92b9e13c65db7cd3c&guid=7066707c5bdc38af1621eaf94a6fe779&id=POTI2NDY5MjQ%3D&idfa=6A76871F-7258-4304-8C7E-F0A0E02A6E27&network=WIFI&operator=%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A_46001&os=ios&os_ver=9.1&ouid=b437dbff9a96ee7f916e4ce869d450657611f643&pid=69b81504767483cf&scale=2&vdid=43C26A77-2450-4AD2-A29E-05A4449E1A47&ver=5.2.1&video_id=XMTM5NTAzMTExNg%3D%3D&_s_=86289609c9dc2350e7a3e944a42d412c&_t_=1448419632

# http://play.youku.com/play/get.json?vid=345653615&ct=12&callback=BuildVideoInfo.response
def get_youku_data(para):
    base_url = 'http://play.youku.com/play/get.json?vid=%s&ct=10'
    _id, data_list, data_list_long = para
    try:
        content = JsonResource(base_url % _id, headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None and content['e']['code']==0:
            data = content['data']
            code = 0
            if 'error' in data:
                code = data['error']['code']
                #-100该视频正在转码中......，请稍后  -101该视频正在审核中......，请稍后  -102该视频已被屏蔽，您可以尝试搜索操作。  -103该视频转码失败，请联系客服  -104视频不存在  -201该视频被设为私密，请联系上传者  -202该视频已经加密，请输入密码  -307观看此节目，请先登录！  -401抱歉，因版权原因无法观看此视频！  -501服务器发生致命错误
                #-204 该视频被设为仅粉丝观看，请关注<a href="%s" target="_blank"><font color="#22B8FE"><u>上传者</u></font></a>。 -205 该视频为私有视频
                if code not in [-100, -101, -102, -103, -104, -201, -202, -204, -205, -307, -401, -501]:
                    print code
                    print data['error']['note']
                    # data_list.append([_id,None,0,None,0,0,None,None,code])
            if 'video' in data and 'seconds' in data['video']:
                data = data['video']
                imageurl = data['logo']
                youku_sid = data['encodeid']
                durationstr = str(data['seconds'])
                if durationstr[0] == '.':
                    duration = 1
                elif '.' in durationstr:
                    duration = int(durationstr[0:durationstr.find('.')])
                    duration += 1
                else:
                    duration = int(durationstr)
                userid = data['userid']
                if 'video' not in data['type']:
                    print 'not video'
                title = data['title'].replace('\r','|').replace('\n','|').replace(',',';')
                tags = '|'.join(data['type'])
                # stream_type = content['data']['stream'][-1]['stream_type']
                if duration < 1500:
                    data_list.append([_id,youku_sid,duration,imageurl,userid,0,tags,title,code])
                else:
                    data_list_long.append([_id,youku_sid,duration,imageurl,userid,0,tags,title,code])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def get_youku_data_old(para):
    base_url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/Pf/4/ctype/12/ev/1'
    _id, data_list, data_list_long = para
    try:
        content = JsonResource(base_url % _id, headers).get_resource()
        if content is None:
            content = JsonResource(base_url % _id, headers).get_resource()
        if content is not None:
            datas = content.get('data', [])
            if len(datas) > 0:
                for data in datas:
                    imageurl = data['logo']
                    # title = data['title']
                    youku_sid = data['vidEncoded']
                    duration = data['seconds']
                    if '.' in duration:
                        duration = duration[0:duration.find('.')]
                    duration = int(duration)
                    title = data['title'].replace('\r','|').replace('\n','|').replace(',',';')
                    up = data['up']
                    down = data['down']
                    tags = '|'.join(data['tags'])

                    if duration < 1500:
                        data_list.append([_id,youku_sid,duration,imageurl,up,down,tags,title,0])
                    else:
                        data_list_long.append([_id,youku_sid,duration,imageurl,up,down,tags,title,0])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def craw_youku(start, end):
    data_list = []
    data_list_long = []
    para_list=[]
    while start < end:
        para_list.append([start, data_list, data_list_long])
        start += 1

    pool_size = 12
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_youku_data, para_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    pool.dismissWorkers(pool_size, do_join=True)

    count = len(data_list)
    if count > 0:
        save(site, data_list)
        print data_list[-1][0]
    count_long = len(data_list_long)
    if count_long > 0:
        save(site+'_long', data_list_long)
    print count, count_long
    return (count + count_long, count_long)


def craw_youku_again(data_list_again):
    data_list = []
    data_list_long = []
    para_list=[]
    for data in data_list_again:
        para_list.append([data, data_list, data_list_long])

    pool_size = 20
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_youku_data, para_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    pool.dismissWorkers(pool_size, do_join=True)
    change_data_list = []
    for data in data_list:
        if data[2] != 0 or data[8] != 0:
            change_data_list.append(data)
    change_count = len(change_data_list)
    count = len(data_list)
    if change_count > 0:
        update(site, change_data_list)
    count_long = len(data_list_long)
    if count_long > 0:
        save(site+'_long', data_list_long)
        delete(site, data_list_long)
    print count-change_count, change_count, count_long
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
    # max_id = get_maxid(site)
    # start = max_id + 1
    start = 356713621 + 10000*500
    print start
    id_start = start
    num = 0
    num_long = 0
    step = 100
    while(True):
        count, count_long = craw_youku(start, start+step)
        if count == 0:
            break
        num += count
        num_long += count_long
        start += step
    save_oplog(site, id_start, num, num_long)
    #
    # data_list_again_all = get_datas(1000000000)
    # count = len(data_list_again_all)
    # data_list_again = []
    # while count > 0:
    #     count -= 1
    #     data_list_again.append(data_list_again_all[count])
    #     if count % 1000 == 0:
    #         print count
    #         print data_list_again[0]
    #         craw_youku_again(data_list_again)
    #         del data_list_again[0: len(data_list_again)]