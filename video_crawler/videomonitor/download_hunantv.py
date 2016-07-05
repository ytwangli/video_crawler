#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
from resource.http import HTMLResource, JsonResource
from resource.database import DataBase
from resource.util import Util
import os
import threadpool
import datetime
import traceback
from hunantv import Hunantv

image_base_path = "/media/3mage/"
video_base_path = "/media/3mage/video/"
site = 'hunantv'
Bad_Datas = []
headers = Hunantv().get_headers()

def download_video(para):
    _id, sid, date_str = para
    try:
        idstr = str(_id)
        video_path = video_base_path+site+'/'+date_str + '/' + idstr + '.flv'
        jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
        jpg_path = jpgdir + idstr + '_20.jpg'
        jpg_path1 = jpgdir + idstr + '_5.jpg'
        if not os.path.exists(jpg_path1):
            video_url_cdn = Hunantv().parse(idstr)
            if video_url_cdn[0] == '-':
                status = video_url_cdn
                Bad_Datas.append([idstr, '', status])
                return None
            if len(video_url_cdn) == 0:
                size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*20)
            else:
                size = HTMLResource('', headers=headers).download_video_ts(video_url_cdn, video_path, 1024*1024*30)
            if size is not None and size > 0:
                # jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
                returncode = Util.movie_split_image(video_path, jpgdir, idstr)
                if os.path.exists(jpg_path):
                    DataBase.update_data(site, idstr, date_str)
                else:
                    if len(video_url_cdn) == 0:
                        size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*40)
                    else:
                        size = HTMLResource('', headers=headers).download_video_ts(video_url_cdn, video_path, 1024*1024*60)
                    if size is not None and size > 0:
                        returncode = Util.movie_split_image(video_path, jpgdir, idstr)
                        if os.path.exists(jpg_path):
                            DataBase.update_data(site, idstr, date_str)
                        elif os.path.exists(jpg_path1):
                            DataBase.update_data(site, idstr, date_str, '1')
                        else:
                            print('remove bad jpg dir: ' + jpgdir)
                            for file in os.listdir(jpgdir):
                                os.remove(os.path.join(jpgdir, file))
                            os.removedirs(jpgdir)
                            Bad_Datas.append([idstr, '', '-99'])
            if os.path.exists(video_path):
                os.remove(video_path)
    except Exception as e:
        print e
        traceback.print_exc()
        print _id

def download():
    runday = datetime.date.today()
    print runday
    data_list = DataBase.get_new_datas(site)
    count = len(data_list)
    if count > 1000:
        del data_list[1000:]
        count = len(data_list)
    if count >= 20:
        print count
        para_list = data_list
        date_str = runday.strftime('%Y%m%d')
        print date_str
        videodir = video_base_path+site+'/'+date_str
        jpgdir = image_base_path+site+'/'+date_str
        if not os.path.exists(jpgdir):
            os.makedirs(jpgdir)
        if not os.path.exists(videodir):
            os.makedirs(videodir)

        for para in para_list:
            para[2] = date_str
        pool_size = 4
        pool = threadpool.ThreadPool(pool_size)
        requests = threadpool.makeRequests(download_video, para_list)
        [pool.putRequest(req) for req in requests]
        pool.wait()
        pool.dismissWorkers(pool_size, do_join=True)
        del para_list[0: len(para_list)]
        DataBase.update_datas(site, Bad_Datas)
        del Bad_Datas[0: len(Bad_Datas)]

        Util.delete_empty_dir(jpgdir)
        if os.path.exists(jpgdir):
            DataBase.insert_pathdata(site, image_base_path, date_str)

def download_by_day():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    runday = datetime.date(2016,1,19)
    days = (today - runday).days + 1
    print runday
    data_list, bad_data_list = DataBase.get_datas(site, 'status=0')

    datas = []
    print len(bad_data_list)
    for bad_data in bad_data_list:
        datas.append([str(bad_data[0]), '', '-1'])
    DataBase.update_datas(site, datas)
    del datas[0: len(datas)]

    count = len(data_list)
    print count
    base_count = ((count - 1) / days) + 1
    print base_count
    para_list = []
    i = 0
    while(i < count):
        para_list.append(data_list[i])
        i += 1
        if i % base_count == 0 or i >= count:
            date_str = runday.strftime('%Y%m%d')
            print date_str
            videodir = video_base_path+site+'/'+date_str
            jpgdir = image_base_path+site+'/'+date_str
            if not os.path.exists(jpgdir):
                os.makedirs(jpgdir)
            if not os.path.exists(videodir):
                os.makedirs(videodir)
            # _id, sid, date_str
            for para in para_list:
                para[2] = date_str
            pool_size = 4
            pool = threadpool.ThreadPool(pool_size)
            requests = threadpool.makeRequests(download_video, para_list)
            [pool.putRequest(req) for req in requests]
            pool.wait()
            pool.dismissWorkers(pool_size, do_join=True)
            del para_list[0: len(para_list)]
            DataBase.update_datas(site, Bad_Datas)
            del Bad_Datas[0: len(Bad_Datas)]
            Util.delete_empty_dir(jpgdir)
            if os.path.exists(jpgdir):
                if len(os.listdir(jpgdir)) > (base_count/2) or i >= count:
                    DataBase.insert_pathdata(site, image_base_path, date_str)
                    runday = runday + oneday

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    download()
    # download_by_day()
