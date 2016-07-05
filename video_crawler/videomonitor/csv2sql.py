#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/opt/video_data/')
from resource.database import DataBase
import os
import MySQLdb

headers = { u'User-Agent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.20 Safari/537.36',
            }
image_base_path = "/media/image/"
vedio_base_path = "/media/video/"
good_download_list = []
good_data_list = []


def move_datas():
    data_list = []
    conn, cur = DataBase.open_conn_video()
    # 239395431
    conn.execute('SELECT id,sid,duration,imageurl,title,play_times,comments,tags,status FROM tudou WHERE duration<1500 and id>=238201414 ORDER BY id ASC')
    count = 0
    for data in cur.fetchall():
        count += 1
        data_list.append(data)
        if count % 10000 == 0:
            print count
            cur.executemany('insert into tudou(id,sid,duration,imageurl,title,play_times,comments,tags,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', data_list)
            del data_list[0: len(data_list)]
            conn.commit()

    if count % 10000 != 0:
        cur.executemany('insert into tudou(id,sid,duration,imageurl,title,play_times,comments,tags,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', data_list)
        del data_list[0: len(data_list)]
        conn.commit()
    DataBase.close_conn(conn, cur)


def save_youku_csv(filename):
    data_list = []
    data_list_long = []
    conn, cur = DataBase.open_conn_video()
    # 239395431
    count = 0
    for line in open(filename, 'r'):
        count += 1
        data = line[0: len(line)-1].split(',')
        if len(data) != 8:
            if len(data) == 7:
                data.append('')
            else:
                print line
                continue
        data.append(0)
        duration = int(data[2])
        if duration>=1500:
            data_list_long.append(data)
        else:
            data_list.append(data)

    cur.executemany('insert into youku(id,sid,duration,imageurl,up,down,tags,title,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', data_list)
    cur.executemany('insert into youku_long(id,sid,duration,imageurl,up,down,tags,title,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)', data_list_long)
    conn.commit()
    DataBase.close_conn(conn, cur)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # move_datas()
    for yid in range(32021, 33324): #31200
        filename = '/media/video/videodata/youku/youku_'+str(yid)+'.csv'
        if not os.path.exists(filename):
            print filename
        # else:
            # save_youku_csv(filename)