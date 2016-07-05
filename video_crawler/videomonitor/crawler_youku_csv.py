#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/opt/video_data/')
from resource.http import HTMLResource,JsonResource
import threadpool
import traceback

headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
            }


def save_csv(handle, result):
    for data in result:
        handle.write('%s,%s,%s,%s,%s,%s,%s,%s\n' % (data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7]))
    handle.flush()

def get_youku_data(para):
    base_url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/Pf/4/ctype/12/ev/1'
    _id, data_list = para
    try:
        content = JsonResource(base_url % _id, headers).get_resource()
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
                data_list.append([_id,youku_sid,duration,imageurl,up,down,tags,title])
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

#314958000
def craw_youku(yid):
    youku_id = yid*10000
    youku_id_min = (yid-1)*10000
    data_list = []
    para_list=[]
    while youku_id > youku_id_min:
        youku_id -= 1
        para_list.append([youku_id,data_list])
    print youku_id_min

    pool_size = 4
    pool = threadpool.ThreadPool(pool_size)
    requests = threadpool.makeRequests(get_youku_data, para_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    pool.dismissWorkers(pool_size, do_join=True)

    count = len(data_list)
    if count>0:
        print count
        # save('youku', data_list)
        handle = open('youku_'+str(yid-1)+'.csv', 'w+')
        save_csv(handle, data_list)
        handle.close()

#(31200,32089) vps
#(31000,31200) null no data
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    yid_start = 31000
    yid_end = 31100
    yid = yid_end
    while yid>yid_start:
        craw_youku(yid)
        yid -= 1
