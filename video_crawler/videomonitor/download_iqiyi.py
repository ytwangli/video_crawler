#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
from resource.http import HTMLResource, HttpResource, JsonResource
from resource.database import DataBase
import os
import datetime
import subprocess
import time
import hashlib
import traceback
from iqiyi import Iqiyi

headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:43.0) Gecko/20100101 Firefox/43.0',
            'Referer': 'http://www.iqiyi.com/common/flashplayer/20151105/MainPlayer_5_2_29_2_c3_3_8_1.swf',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            # 'Cookie': 'P00001=afNHV8CBb6BHl2OG2yhJ5MWWSJm1m2BHoLac9zQi8xq0YNom49f',  # dolby_account_50@qiyi.com
            }

f4v_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.99 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
            }

mp4_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.99 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'http://m.iqiyi.com',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
            }

image_base_path = "/media/0mage/"
video_base_path = "/media/image/video/"
site = 'iqiyi'

def movie_split_image(filepath, jpgdir, idstr, start=0, end=300):
    returncode = -1
    # ffmpeg -i 348857801.mp4 -vf fps=15 -qscale 2 -f image2 -c:v mjpeg 348857801/348857801%d.jpg
    # ffmpeg -i /mediaideo/iqiyi504p/373009300/1.f4v -vf fps=12.5 -qscale 2 -f image2 -c:v mjpeg 1_%d.jpg
    if not os.path.exists(jpgdir):
        os.makedirs(jpgdir)
    # 5s per image
    # cmd_line = 'cd '+jpgdir+' && ffmpeg -i '+filepath+' -vf fps=12.5 -qscale 2 -f image2 -c:v mjpeg -ss 0 -t 300 '+str(idstr)+'_%d.jpg'
    cmd_line = 'cd %s && ffmpeg -i %s -vf fps=12.5 -qscale 2 -f image2 -c:v mjpeg -ss %s -t %s %s_%s.jpg' % (jpgdir, filepath, start, end, idstr, '%d')
    # cmd_line = 'cd '+jpgdir+' && ffmpeg -i '+filepath+' -vf fps=0.2 -qscale 2 -f image2 -c:v mjpeg -ss 0 -t 120 '+idstr+'_%d.jpg'
    print cmd_line
    p = subprocess.Popen(cmd_line, shell=True)
    returncode = p.wait()
    return returncode


def download_mp4(para):
    base_key = '3de6a750a4044c42aa190b8be62e82aa'
    id, doc_id, tvid, vid, link = para
    link = link.replace('www.iqiyi.com', 'm.iqiyi.com')
    timestamp = str(int(time.time()*1000))
    token = hashlib.md5((timestamp+base_key+tvid)).hexdigest()
    url = 'http://cache.m.iqiyi.com/jp/tmts/%s/%s/?uid=&cupid=qc_100001_100186&platForm=h5&type=mp4&rate=1&src=d846d0c32d664d32b6b54ea48997a589&sc=%s&t=%s&__jsT=sgve' % (tvid, vid, token, timestamp)
    # url = 'http://cache.m.iqiyi.com/jp/tmts/%s/111/?uid=2093402236&cupid=&type=mp4' % tvid
    headers['Refer'] = link
    content = JsonResource(url, headers=headers).get_resource()
    # print content
    size = 0
    filepath = video_base_path+site+'/'+tvid+'.mp4'
    if content is not None and 'data' in content and 'm3u' in content['data']:
        video_url = content['data']['m3u'] + '&qypid=223530900_31'
        down_vid = content['data']['vid']
        # video_url = 'http://data.video.iqiyi.com' + video_url[video_url.index('/', 7):]
        # 已下载过了，返回文件大小做比对
        web_size = HttpResource(video_url, headers=headers).get_length()
        mp4_headers['Refer'] = link
        size = HttpResource(video_url, headers=headers).download_mp4(filepath)
        if size is None or size != web_size:
            print('Error size: %s, %s, %s' % (size, web_size, filepath))
    else:
        print('--no mp4: %s, %s' % (doc_id, tvid))
    return size


def copy(idstr):
    cmd_line = 'scp -r /media/image/iqiyi/'+idstr+' x1:/media/image/iqiyi/'
    p = subprocess.Popen(cmd_line, shell=True)
    returncode = p.wait()
    if returncode != 0:
        print returncode
        print cmd_line

def download_video(para):
    _id, vid, start_time, video_title, link, album_id, online_time, video_url = para
    tvid = str(_id)
    try:
        video_path = video_base_path+site+'/'+ tvid + '.flv'
        jpgdir = image_base_path+site+'/' + tvid + '/'
        jpg_path = jpgdir + tvid + '_1499.jpg'
        if not os.path.exists(jpgdir + tvid + '_599.jpg'):
            if not os.path.exists(video_path):
                if video_url is None:
                    video_url_cdn = Iqiyi().parse(tvid, vid)
                    if video_url_cdn is not None:
                        size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*200)
                    else:
                        print video_title
                else:
                    size = HTMLResource(video_url, headers=headers).download_video(video_path, 1024*1024*200)
            if os.path.exists(video_path):
                # jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
                returncode = movie_split_image(video_path, jpgdir, tvid, start=start_time, end=start_time+120)
                if os.path.exists(jpg_path):  # returncode == 0:
                    # copy(tvid)
                    update_data(tvid, video_title, link, album_id, online_time, start_time)
                else:
                    os.remove(video_path)
                    size = 0
                    if video_url is None:
                        video_url_cdn = Iqiyi().parse(tvid, vid)
                        if video_url_cdn is not None:
                            size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*200)
                    else:
                        size = HTMLResource(video_url, headers=headers).download_video(video_path, 1024*1024*200)
                    if size is not None and size > 0:
                        returncode = movie_split_image(video_path, jpgdir, tvid, start=start_time, end=start_time+120)
                        if os.path.exists(jpg_path):  # returncode == 0:
                            # copy(tvid)
                            update_data(tvid, video_title, link, album_id, online_time, start_time)
                        else:
                            print 'image not full error:' + tvid
    except Exception as e:
        print e
        traceback.print_exc()
        print _id


def download_album_video(para):
    _id, vid, album_id, start_time, video_title, link, online_time, video_url = para
    tvid = str(_id)
    album_idstr = '_' + str(album_id)
    try:
        video_path = video_base_path+site+'/'+ tvid + '.flv'
        jpgdir = image_base_path+site+'/' + album_idstr + '/'
        jpg_path = jpgdir + album_idstr + '_10.jpg'
        if not os.path.exists(jpg_path):
            if not os.path.exists(video_path):
                if video_url is None:
                    video_url_cdn = Iqiyi().parse(tvid, vid)
                    if video_url_cdn is not None:
                        size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*200)
                else:
                    size = HTMLResource(video_url, headers=headers).download_video(video_path, 1024*1024*200)
            if os.path.exists(video_path):
                # jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
                returncode = movie_split_image(video_path, jpgdir, album_idstr, start=0, end=start_time)
                if os.path.exists(jpg_path):  # returncode == 0:
                    # copy(album_idstr)
                    update_album_datas(album_idstr, video_title, link, album_id, online_time, start_time, tvid)
                else:
                    os.remove(video_path)
                    size = 0
                    if video_url is None:
                        video_url_cdn = Iqiyi().parse(tvid, vid)
                        if video_url_cdn is not None:
                            size = HTMLResource(video_url_cdn[0], headers=headers).download_video(video_path, 1024*1024*200)
                    else:
                        size = HTMLResource(video_url, headers=headers).download_video(video_path, 1024*1024*200)
                    if size is not None and size > 0:
                        returncode = movie_split_image(video_path, jpgdir, album_idstr, start=0, end=start_time)
                        if os.path.exists(jpg_path):  # returncode == 0:
                            # copy(album_idstr)
                            update_album_datas(album_idstr, video_title, link, album_id, online_time, start_time, tvid)
                        else:
                            print 'image not full error:' + album_idstr
    except Exception as e:
        print e
        traceback.print_exc()
        print album_idstr

def update_data(tvid, video_title, link, album_id, online_time, start_time):
    conn, cur = DataBase.open_conn_video()
    image_dir = image_base_path+site+'/' + tvid
    exe_time = datetime.datetime.now()
    date_str = time.strftime("%Y%m%d", time.localtime())
    if len(online_time) == 19:
        online_time = online_time[0:10]
    cur.execute( 'insert into iqiyidata(host,site,row_type,video_title,link,tvid,album_id,online_time,image_dir,start_time,key_type,code_flag,used_flag,new_flag,date_str,create_date,update_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (2,'iqiyi', 1, video_title,link,tvid,album_id,online_time,image_dir,start_time, 'all', 0, 1, 1, date_str,exe_time,exe_time))
    conn.commit()
    DataBase.close_conn(conn, cur)

def update_album_datas(album_id_str, video_title, link, album_id, online_time, start_time, tvid):
    conn, cur = DataBase.open_conn_video()
    image_dir = image_base_path+site+'/' + album_id_str
    exe_time = datetime.datetime.now()
    date_str = time.strftime("%Y%m%d", time.localtime())
    if len(online_time) == 19:
        online_time = online_time[0:10]
    index = video_title.rfind('第')
    video_title = video_title[0: index] + '_ 片头曲'
    cur.execute( 'insert into iqiyidata(host,site,row_type,video_title,link,tvid,album_id,online_time,image_dir,start_time,key_type,code_flag,used_flag,new_flag,date_str,create_date,update_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (2,'iqiyi', 0, video_title,link,tvid,album_id,online_time,image_dir,start_time, 'all', 0, 1, 1, date_str,exe_time,exe_time))
    conn.commit()
    DataBase.close_conn(conn, cur)

def get_datas():
    conn, cur = DataBase.open_conn_qidun()
    iqiyi_detail_keys = set()  # 用于唯一性校验
    copyright_videos = {}  # 需要下载的版权视频列表
    cur.execute("SELECT id,doc_id,video_no,tvid,vid,link,video_title,album_id,online_time,start_time FROM iqiyi_copyright_details order by doc_id, tvid desc;")
    for data in cur.fetchall():
        id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = data
        # print tvid
        key = tvid
        if key not in iqiyi_detail_keys:
            iqiyi_detail_keys.add(key)
            if album_id not in copyright_videos:
                copyright_videos[album_id] = [data]
            else:
                copyright_videos[album_id].append(data)
    print len(copyright_videos)
    DataBase.close_conn(conn, cur)
    return copyright_videos

def get_data(tvid):
    conn, cur = DataBase.open_conn_qidun()
    cur.execute("SELECT id,doc_id,video_no,tvid,vid,link,video_title,album_id,online_time,start_time FROM iqiyi_copyright_details where tvid='"+str(tvid)+"';")
    datas = cur.fetchall()
    DataBase.close_conn(conn, cur)
    if len(datas) == 1:
        return datas[0]
    else:
        print 'error tvid:' + str(tvid)
        return None

def download():
    copyright_videos = get_datas()
    for album_id in copyright_videos:
        download_videos = []
        videos = copyright_videos[album_id]
        videos_len = len(videos)

        is_need_start_split = False
        if videos_len > 1:
            max_data = videos[0]
            max_start_time = int(max_data[-1])
            for data in videos:
                start_time = int(data[-1])
                if start_time > max_start_time:
                    max_data = data
                    max_start_time = start_time
            if max_start_time > 3:
                is_need_start_split = True
                id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = max_data
                download_album_video([tvid, vid, album_id, start_time, video_title, link, online_time, None])

        already_down_num = 0
        for data in videos:
            tvid = data[3]
            if os.path.exists(image_base_path+site+'/' + tvid + '/' + tvid + '_599.jpg'):
                already_down_num += 1

        if videos_len < 7:
            download_videos.extend(videos)
        elif videos_len < 20:
            if already_down_num == 0:
                download_videos.append(videos[0])
                download_videos.append(videos[videos_len / 2])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 1:
                download_videos.append(videos[videos_len / 2])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 2:
                download_videos.append(videos[videos_len - 1])
        else:
            if already_down_num == 0:
                download_videos.append(videos[0])
                download_videos.append(videos[videos_len / 4])
                download_videos.append(videos[videos_len / 2])
                download_videos.append(videos[videos_len - (videos_len / 4)])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 1:
                download_videos.append(videos[videos_len / 4])
                download_videos.append(videos[videos_len / 2])
                download_videos.append(videos[videos_len - (videos_len / 4)])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 2:
                download_videos.append(videos[videos_len / 2])
                download_videos.append(videos[videos_len - (videos_len / 4)])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 3:
                download_videos.append(videos[videos_len - (videos_len / 4)])
                download_videos.append(videos[videos_len - 1])
            elif already_down_num == 4:
                download_videos.append(videos[videos_len - 1])
        for data in download_videos:
            id, doc_id, video_no, tvid, vid, link, video_title, album_id, online_time, start_time = data
            start_time = int(start_time)
            if start_time < 0:
                start_time = 0
            if is_need_start_split:
                download_video([tvid, vid, start_time, video_title, link, album_id, online_time, None])
            else:
                download_video([tvid, vid, 0, video_title, link, album_id, online_time, None])


def get_list(copyright_videos):
    conn, cur = DataBase.open_conn_video()
    videos = []  # 需要下载的版权视频列表
    cur.execute("SELECT id,image_dir FROM iqiyidata WHERE `tvid` in (356215200, 384926000, 384925800, 374634900, 373009300, 384548400, 384551800, 385745300);")
    data_list = cur.fetchall()
    for data in data_list:
        id, image_dir = data
        if image_dir.endswith('/'):
            image_dir = image_dir[0: len(image_dir)-1]
        tvid_x = int(image_dir.replace('/media/0mage/iqiyi/', '').replace('_', '').replace('/', ''))
        is_in = False
        if '_' in image_dir:
            for key, videos in copyright_videos.iteritems():
                for video in videos:
                    id_x, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = video
                    if int(album_id) == tvid_x:
                        is_in = True
                        if len(online_time) == 19:
                            online_time = online_time[0:10]
                        if '第' in video_title:
                            if '季' in video_title:
                                video_title = video_title[0: video_title.find('第', video_title.find('季')+1)]
                            else:
                                video_title = video_title[0: video_title.find('第')]
                        video_title = video_title + '_ 片头曲'
                        if start_time < 0:
                            start_time = 0
                        cur.execute("UPDATE iqiyidata SET video_title='%s', link='%s', tvid='%s', album_id='%s', online_time='%s', image_dir='%s', start_time='%s' WHERE id = %s" % (video_title, link, tvid, album_id, online_time, image_dir, start_time, id))
                        break
        else:
            for key, videos in copyright_videos.iteritems():
                for video in videos:
                    id_x, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = video
                    if int(tvid) == tvid_x:
                        is_in = True
                        if len(online_time) == 19:
                            online_time = online_time[0:10]
                        if start_time < 0:
                            start_time = 0
                        cur.execute("UPDATE iqiyidata SET video_title='%s', link='%s', tvid='%s', album_id='%s', online_time='%s', image_dir='%s', start_time='%s' WHERE id = %s" % (video_title, link, tvid, album_id, online_time, image_dir, start_time, id))
                        break
        # if is_in:
        #     cur.execute("UPDATE iqiyidata SET video_title='%s', link='%s', tvid='%s', album_id='%s' WHERE id = %s" % (video_title, link, tvid, album_id, id))
        # else:
        #     print id
        #     cur.execute("DELETE FROM iqiyidata WHERE id = %s" % (id))
    conn.commit()
    DataBase.close_conn(conn, cur)

def split():
    urls = {

    }
    video_path = ''
    start_time_max = 0
    album_data = None
    # is_movie = True
    is_movie = False
    for url in urls:
        # &start=9175040&end=58550527
        url = url[0: url.find('&range=')]
        index = url.find('&qypid=')+7
        tvid = url[index: url.find('_', index)]
        video_path = video_base_path+site+'/'+ tvid + '.flv'
        data = get_data(tvid)
        _id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = data
        print video_title
        if is_movie:
            start_time = 0
        download_video([tvid, vid, start_time, video_title, link, album_id, online_time, url])
        if start_time > start_time_max:
            start_time_max = start_time
            album_data = data
    if not is_movie:
        _id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = album_data
        download_album_video([tvid, vid, album_id, start_time, video_title, link, online_time, None])

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # download()
    # get_list(get_datas())
    urls = [
        # &qypid=366566000_11&
        # # 奔跑吧小凡 http://www.iqiyi.com/v_19rrnrfkm4.html
        # 'http://60.210.17.239/videos/vip/20150522/93/06/40db8db804994c27d0526038e34008bf.f4v?key=0c3a9fdc77a9fe2a3b3efab1547dab2c6&src=iqiyi.com&t=51a57dc2ecd37d249e2eb63dfb26637e&cid=afbe8fd3d73448c9&vid=7e619c6d230b49c4172bfb23b5fe6fe6&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=366566000_11&ran=732&uuid=ca6c0ef0-560b51b0-38',
        # # 我滴个神啊 http://www.iqiyi.com/v_19rrog5754.html
        # 'http://60.210.17.187/videos/vip/20150827/21/b8/c8bcc2e988074c438d8b8949926caa4b.f4v?key=0a99c40c177756b9933a6e961f387b449&src=iqiyi.com&t=8b49e2d7672c8cc8dd4f75e470d037b9&cid=afbe8fd3d73448c9&vid=ea2107ee712cef6548e90b2cac0af878&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=374404100_11&ran=1427&uuid=ca6c0ef0-560b5195-38',
        # # 二龙湖浩哥之狂暴之路 http://www.iqiyi.com/v_19rro95fns.html
        # 'http://111.206.23.147/videos/vip/20150820/e0/10/55c8e02815b78c0baa0f5a738c272489.f4v?key=09aa2f4c65d8a24578915a4c8b409e59f&src=iqiyi.com&t=7ceeff03e442a25e90e9f69008a71d60&cid=afbe8fd3d73448c9&vid=14af811245e14d8cf8abf1b55862277b&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=387920100_11&ran=431&uuid=ca6c0ef0-560b5160-38',
        # 'http://111.206.23.145/videos/vip/20151229/73/27/ccb93853aa895c79610cc8576ac794f1.f4v?key=0aedf7497357d63a51754d5510df52f90&src=iqiyi.com&qd_tvid=430417500&qd_vipres=2&qd_index=1&qd_aid=202842701&qd_stert=0&qd_scc=cee6876d32b142877a29f4684bd3809a&qd_sc=08d7b7f226f3c0410abf75939741e52c&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374910000&qd_vip=1&t=1453374916_75dae8a61f365ced0f0d666b90749064&cid=afbe8fd3d73448c9&vid=db883ccfe425ba624bc3127b142c3fae&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=430417500_11&ran=2772&uuid=ca6c0ef0-56a0bdc4-57&range=0-62202133&qypid=430417500_01010011010000000000_5&ran=3075'
        # 蜀山战纪第一季  _202550601
        #     "1": "http://60.210.17.196/videos/vip/20150921/72/24/be484e2e9ba68dcdd2efb1050a8d4dde.f4v?key=054160f2deb4645a987ab8973fccc4255&src=iqiyi.com&t=acf2d9719fd04b4438e03e7d446ae25a&cid=afbe8fd3d73448c9&vid=77606d31c61650cbfac09e1ee8f6c350&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399717900_11&ran=1271&uuid=ca6c0ef0-560141ab-39",
        #     "2": "http://60.210.17.203/videos/vip/20150921/8a/a1/bff5383b6e1e5a425a0b4d90c2587bd1.f4v?key=0af6927c80ed45c8b4d223ac10ef79d05&src=iqiyi.com&t=03f1515f6502eaf4f0a14cacb49eafd7&cid=afbe8fd3d73448c9&vid=ad0c9a383927c08bdbeaf2a076eaae52&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399720800_11&ran=421888&uuid=ca6c0ef0-56014350-5f",
        #     "3": "http://60.210.17.173/videos/vip/20150921/cf/28/cc77f56cbeaff5179078d627128327c1.f4v?key=0109ac7b27fe427d74032b03b591abc7f&src=iqiyi.com&t=1c5a6adba385441b5d5a05c3fe65eaed&cid=afbe8fd3d73448c9&vid=b08a8f7b1a26b85388d773cf0b41c774&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399723400_11&ran=492922&uuid=ca6c0ef0-56014397-5f",
        #     "4": "http://60.210.17.192/videos/vip/20150921/40/bc/381fe4eb8808a5c2832051afd985f600.f4v?key=022196a04a649babfb2097e0808d81969&src=iqiyi.com&t=04e026377845589318086e57d0c8f12f&cid=afbe8fd3d73448c9&vid=38397f1ddc1b5dd226693fd7d816d77f&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399724500_11&ran=507331&uuid=ca6c0ef0-560143a5-5f",
        #     "5": "http://60.210.17.185/videos/vip/20150921/89/d2/b6c5cb1651976096b7128af134da0605.f4v?key=05b351168b1cfb8a69a8f6a895e58231d&src=iqiyi.com&t=8cb178427d00288acd25ecb867e8af29&cid=afbe8fd3d73448c9&vid=a945336910d634095a82475e75f91fcc&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399725000_11&ran=545948&uuid=ca6c0ef0-560143cc-5f",
        #     "6": "http://60.210.17.207/videos/vip/20150921/cb/3d/9cb245b33f3be3bfedc0f3d57e8520d4.f4v?key=0529e97e58de7174b270c26afb6f5e655&src=iqiyi.com&t=183d2eabb934fdb80875ca3356ab792b&cid=afbe8fd3d73448c9&vid=2432e726075eb63d05fd0545be6f0700&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399725400_11&ran=561126&uuid=ca6c0ef0-560143db-5f",
        #     "7": "http://60.210.17.213/videos/vip/20150921/7a/80/a1088af44ec266f26439e8c3278ffe9b.f4v?key=00422a4c36b2d0a0a5d46f1df5ed216bd&src=iqiyi.com&t=d62bb54cb72db47cc14b6e663d599c9b&cid=afbe8fd3d73448c9&vid=2ac5414e3fb6e65101b1d76b09f3372b&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399725800_11&ran=576269&uuid=ca6c0ef0-560143ea-5f",
        #     "8": "http://60.210.17.177/videos/vip/20150921/14/45/44e90cf7ab13cf9ae9fed8b953ab897a.f4v?key=0422ba929e8831575d71322bb2b3dfdc5&src=iqiyi.com&t=753927af3136ec800902b90707318e13&cid=afbe8fd3d73448c9&vid=bcc97f175908ca2eba2b06f69cdd36f7&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399726200_11&ran=585135&uuid=ca6c0ef0-560143f3-5f",
        #     "9": "http://60.210.17.242/videos/vip/20150921/93/54/b13f8148d40d3e87acd52c243769ca36.f4v?key=0568a53ed6e43b6ebc72283bb2ae08d27&src=iqiyi.com&t=f17d3d65665908b9f2bc940cad5aff28&cid=afbe8fd3d73448c9&vid=9e729c24dd4da4b183d0e44921681257&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399728400_11&ran=597040&uuid=ca6c0ef0-560143ff-5f",
        #     "10": "http://60.210.17.199/videos/vip/20150921/2b/ed/02fd22c7d1acef3e30112d3d8aa249fb.f4v?key=09826118fdd92919d8448bad43e505fa4&src=iqiyi.com&t=81f4ba895d1f16e49c2c17bbee2878c7&cid=afbe8fd3d73448c9&vid=afd22799ea29bbd21f0577a8f7d1c29b&QY00001=2047395208&qyid=b5889a008520488d973d1ef8a12509ef&qypid=399726900_11&ran=611821&uuid=ca6c0ef0-5601440e-5f",

        # 蜀山战纪第二季  203062601
        # 'http://60.210.17.203/videos/vip/20151020/b0/e0/55073ebec1f697aa14cb28e65e5fd97b.f4v?key=05e796062544345c5d033e6ca7ccbb681&src=iqiyi.com&t=06e3219369dc80a9f6997a374e80359a&cid=afbe8fd3d73448c9&vid=091092b7843b1669e496376b689d8398&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409319100_11&ran=2062688&uuid=ca6c0ef0-5628d1df-5c&range=0-8191&ran=2062770',
        # 'http://60.210.17.195/videos/vip/20151020/ce/20/6acc50bee34723b6bad7a64e33d84d0b.f4v?key=088423d7a1712d19ad23ba97963b1a8f7&src=iqiyi.com&t=41af7c7dfbf27d2754796ccab65cefbf&cid=afbe8fd3d73448c9&vid=20cc77d29f39c3c48ee053702c974fcf&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409313100_11&ran=2092178&uuid=ca6c0ef0-5628d1fd-5c&range=0-3932159&ran=2092221'
        # 'http://60.210.17.203/videos/vip/20151020/ce/20/6acc50bee34723b6bad7a64e33d84d0b.f4vcrc?key=088423d7a1712d19a96ad5feff36d4576&src=iqiyi.com&t=d06803702fc4a39ff0955951ebbdac3b&cid=afbe8fd3d73448c9&vid=20cc77d29f39c3c48ee053702c974fcf&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409313100_11&ran=1332201&uuid=ca6c0ef0-5628cf05-19',
        # 'http://60.210.17.193/videos/vip/20151020/94/f7/dd474c8c1f61ec629d8822a18b60e9df.f4v?key=07ef41a5d8c22fbd11d62a0821eede21b&src=iqiyi.com&t=7a2144db9cddc4cb6b4ca95246a9abbb&cid=afbe8fd3d73448c9&vid=92d9e55ea855906aed97296b03fff46c&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409314500_11&ran=1373017&uuid=ca6c0ef0-5628cf2e-19&range=12320768-25165823&ran=1373381',
        # 'http://60.210.17.238/videos/vip/20151020/3f/0f/7214768faeaee32bf64128d9def198a1.f4v?key=00e730fa15cfc4ed5cc90d5e9c503d58b&src=iqiyi.com&t=616c61fc63a08656965dc8591cb2e66c&cid=afbe8fd3d73448c9&vid=c1f91292d164e7d0c2f50416efacbcb2&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409316100_11&ran=1384312&uuid=ca6c0ef0-5628cf39-5c&range=12582912-26476543&ran=1385491',
        # 'http://60.210.17.199/videos/vip/20151020/c5/ba/319fbe4873dd65797402e35f5bf36e31.f4v?key=080b3b1608c8f199d167efb3bb3eacb46&src=iqiyi.com&t=6be1a5580655e979fa48d245289f1009&cid=afbe8fd3d73448c9&vid=75e2392b9b6ef761964d9ab5bef60442&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409317700_11&ran=1399947&uuid=ca6c0ef0-5628cf48-5c&range=12845056-22020095&ran=1400472',
        # 'http://111.206.23.130/videos/vip/20151020/65/37/fd0dd0da48337d6fb622a04089ceebf5.f4v?key=09a2aef22579cbe1f305f846fcb77a5eb&src=iqiyi.com&t=73ca2b2a72c2f1df2e18c19a1586f1f8&cid=afbe8fd3d73448c9&vid=919659fb3df0392a6c8a82e2ebe4e5c2&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409320700_11&ran=1583163&uuid=ca6c0ef0-5628d000-5f&range=12058624-29097983&ran=1583503',
        # 'http://60.210.17.185/videos/vip/20151020/7a/20/8eb1d30c941bbca3e8d80325c4e8b5b9.f4v?key=09d62f54c4e665edabcc1d44acddc977b&src=iqiyi.com&t=7569fcb2c955191a7d8939372e4be4fd&cid=afbe8fd3d73448c9&vid=468b7c832cea271f7ac14ca2c87fb228&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409322900_11&la=CNC|QiYi-202.108.14.240&li=zibo_cnc&lsp=-1&lc=176&ran=1640600&uuid=ca6c0ef0-5628d039-5f&range=1048576-12845055&ran=1643582',
        # 'http://60.210.17.190/videos/vip/20151020/9a/e2/dd99338e6674e000ac81ae28d6f71857.f4v?key=0ce37cfef69bf720259591cd35785f68&src=iqiyi.com&t=f2170a5e9146013c09fb2da308992fc6&cid=afbe8fd3d73448c9&vid=f25c176353c6fbb26878deafdecffe8c&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409324500_11&ran=1652175&uuid=ca6c0ef0-5628d045-5f&range=11272192-20709375&ran=1652665',
        # 'http://60.210.17.192/videos/vip/20151020/bc/3f/0ae72d0a4769a6b7ac0548cbb162eb26.f4v?key=0c1cbc1d5e037f42b1b79a2eea73f0aea&src=iqiyi.com&t=b19cc79e5cb62bb7ca969742ff024059&cid=afbe8fd3d73448c9&vid=1a4f3b5ad3d3f7d6c5dccf47dfa8a67b&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409325800_11&ran=1662887&uuid=ca6c0ef0-5628d04f-5f&range=13369344-23855103&ran=1663292',
        # 'http://60.210.17.236/videos/vip/20151020/94/63/ebdcbec1511c2deb00a4386cc3162417.f4v?key=03d4a71c1844f9042a07db756b5640c1&src=iqiyi.com&t=044a60560ba171e7bacec5961ec7ca00&cid=afbe8fd3d73448c9&vid=5f7c75ec6b1438d91b515933a1166306&QY00001=2047395208&qyid=cd55244c729ac40adc8bfd9b05185ed4&qypid=409327500_11&ran=1671975&uuid=ca6c0ef0-5628d059-5f&range=11010048-11534335&ran=1678514',

        # # 蜀山战纪第三季  203166401
        # 'http://60.210.17.203/videos/vip/20151118/62/fd/f98a92f1f3095fbc4e4b9d6f8071ffe2.f4v?key=0cb1669759c4005d7d7a3886a3438d8d3&src=iqiyi.com&t=be3f9942d66b073f5774da5f1b6ffb5e&cid=afbe8fd3d73448c9&vid=1d7d9233422e24a3d8d2e8ef958193c6&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420157900_11&s=2932536.296723914&bt=388895&z=zibo_cnc&la=CNC|QiYi-202.108.14.240&li=zibo_cnc&lsp=3363&lc=324&ran=8238&uuid=ca6c0ef0-5653c87b-19&range=0-57147391&qypid=420157900_01010011010000000000_5&ran=8284',
        # 'http://60.210.17.190/videos/vip/20151118/10/a0/149c556016fbd16d1e21ea388aeec843.f4v?key=0d847a9b5a3f338097d60b5d02770d447&src=iqiyi.com&t=d072c31789e6140caae136b019b0e2df&cid=afbe8fd3d73448c9&vid=1fdc5fc77839640fd41065ca9a94f36f&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420152300_11&ran=619058&uuid=ca6c0ef0-5653cd0f-39&range=58720256-123469823&qypid=420152300_01010011010000000000_5&ran=620109',
        # 'http://60.210.17.203/videos/vip/20151118/21/24/590cfb25e96c3b34c718317df2fbcdb9.f4v?key=06d090bd6503ad20bd16a6f15022a8da0&src=iqiyi.com&t=1c28e45e6cd17af60c48dadb6cbf2d72&cid=afbe8fd3d73448c9&vid=fe2665b21f0aaab454f834582ca19c7b&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420158500_11&ran=633425&uuid=ca6c0ef0-5653cd1d-39&start=58720256&end=138412032&qypid=420158500_01010011010000000000_5&ran=634776',
        # 'http://60.210.17.186/videos/vip/20151118/a9/95/e7a6434da87b727278a1148e544e876d.f4v?key=04351722374314cfd2c034b0bcb158489&src=iqiyi.com&t=f539b653b3184b28cc2fe6506dfa3cec&cid=afbe8fd3d73448c9&vid=33eb005b025f91aa967ced4d618bd101&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420156800_11&ran=58722&uuid=ca6c0ef0-5653c8ae-19&range=67895296-151257087&qypid=420156800_01010011010000000000_5&ran=523721',
        # 'http://60.210.17.177/videos/vip/20151118/9c/a8/61db0450a6e9abeb936916421c3bf5f6.f4v?key=0b1e891d5a95f31fd814f5066e17a8147&src=iqiyi.com&t=5e84aa7d06c144dae468034e1295327f&cid=afbe8fd3d73448c9&vid=d119c85d05a58c841f0c48ff7c884879&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420172200_11&ran=1898&uuid=ca6c0ef0-5653ce00-24&start=58720256&end=134217728&qypid=420172200_01010011010000000000_5&ran=2455',
        # 'http://60.210.17.184/videos/vip/20151118/5a/ee/a968868c30dc0603aa75070748a1c1bc.f4v?key=06b7245cd8b2058acc67d9c0e7be55732&src=iqiyi.com&t=9a4786deef054efad1d84cd67f52b1de&cid=afbe8fd3d73448c9&vid=f1757c5bc165630caabf692f377b9597&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420172500_11&ran=42060&uuid=ca6c0ef0-5653ce28-24&range=58720256-123469823&qypid=420172500_01010011010000000000_5&ran=42573',
        # 'http://60.210.17.174/videos/vip/20151118/ce/7b/4272512b899f1f431a4f858638b5db7d.f4v?key=08a6078f266957c1a289526e6d1087b09&src=iqiyi.com&t=f8430273380cee4fb774449c4f603896&cid=afbe8fd3d73448c9&vid=cbfe2a95b90c852b913356120e938896&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420172900_11&ran=78985&uuid=ca6c0ef0-5653ce4d-24&start=58720256&end=124256256&qypid=420172900_01010011010000000000_5&ran=79984',
        # 'http://60.210.17.182/videos/vip/20151118/a7/ac/670f217b9a2e8a3401febcb7e7d4db60.f4v?key=0688ef5376c84a52bb8ff345fc321f4ce&src=iqiyi.com&t=95c92dfa10e5a3af239f2881146389f5&cid=afbe8fd3d73448c9&vid=3e7f801716349968cd863d5b79dbbb98&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420173200_11&ran=94587&uuid=ca6c0ef0-5653ce5d-24&start=58720256&end=127139840&qypid=420173200_01010011010000000000_5&ran=95444',
        # 'http://60.210.17.190/videos/vip/20151118/04/f7/173e16f11b28672e06e863d96644cb76.f4v?key=0dcf534477393a31aef7fba72a0bd3dae&src=iqiyi.com&t=4a31aaa7ae90a0a016cf009256ed4fec&cid=afbe8fd3d73448c9&vid=67f7e4ce23056b4270137c676dffca18&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420173500_11&ran=148227&uuid=ca6c0ef0-5653ce93-24&start=58720256&end=136052736&qypid=420173500_01010011010000000000_5&ran=148712',
        # 'http://111.206.23.17/videos/vip/20151118/d3/b5/bd663a58abcf7741c8d8a07b43e99af9.f4v?key=08dec14c8795603005e4d4ed288d6ce5c&src=iqiyi.com&t=f5c6e648e754b9c766573b3ca6f7d6b7&cid=afbe8fd3d73448c9&vid=47ec17e9922c087f93160e828ce0b4a1&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=420174300_11&ran=166061&uuid=ca6c0ef0-5653cea5-24&start=58720256&end=137887744&qypid=420174300_01010011010000000000_5&ran=166687',

        # # 蜀山战纪第四季  203166501
        # 'http://111.206.23.149/videos/vip/20151224/33/e3/5a85da0367552d0363252a9988b5af89.f4v?key=004854d9c7140cf3fd5f21b2c462129d4&src=iqiyi.com&qd_tvid=431330300&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=2918a3b21bce26c955d27ae9679f6129&qd_sc=71c33205cf8054b1dac50ac873ebe345&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218824000&qd_vip=1&t=1451218835_115b99ee8eac3b4d4217a56d291c8990&cid=afbe8fd3d73448c9&vid=df62e25bb8b6859425109dd41b4ad293&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431330300_11&ran=916036&uuid=ca6c0ef0-567fd79a-24',
        # 'http://111.206.23.131/videos/vip/20151224/ee/de/5d68fd360e45885fa42f76db677c888e.f4v?key=0828f18b96e49371c8ee5614749b44944&src=iqiyi.com&qd_tvid=431330900&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=c5a7bd6078821c48b7d5255e1659101d&qd_sc=fbc8e943a475752ba8c8bc8c57d96362&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451217940000&qd_vip=1&t=1451217951_b8ab3eaef07c3a6b8cc21b8d0b544260&cid=afbe8fd3d73448c9&vid=5c0e01949f532676e804da3b9fd9e955&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431330900_11&ran=31572&uuid=ca6c0ef0-567fd429-24',
        # 'http://111.206.23.132/videos/vip/20151224/5b/fb/8009186bb29d16b5512d6e1e69d6bdcb.f4v?key=01a6cdf9bc97b3b95e35f4937e8e5455c&src=iqiyi.com&qd_tvid=431331200&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=1ba13e9d1630889dc0cbf47e1d06d6e0&qd_sc=15d03ecbd9c153617614bc4d81537946&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451217974000&qd_vip=1&t=1451217976_01fcd9982d778e82bee84bb4fa177717&cid=afbe8fd3d73448c9&vid=0d9ef8601ffa86d31330c9a1fa464a15&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431331200_11&ran=56170&uuid=ca6c0ef0-567fd442-24',
        # 'http://111.206.23.134/videos/vip/20151224/d3/1e/82044812b2fce57fe7ca9d4b9fd0b680.f4v?key=09b8f3f9ffdeb95029d08fe86dae6bf47&src=iqiyi.com&qd_tvid=431331900&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=0b6e7f2c6f966d2f2e05e020a30e5b37&qd_sc=f25e6521ca63bae2ad7b9b0d736c7f0e&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218093000&qd_vip=1&t=1451218095_be09f9f53dcd3f4dd10e45216674e61a&cid=afbe8fd3d73448c9&vid=e7d3bcf53b91a1a65f0b70727e0ed732&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431331900_11&ran=175189&uuid=ca6c0ef0-567fd4b6-24',
        # 'http://111.206.23.142/videos/vip/20151224/c6/5b/fef4eea3338e7d67b39e3f61ba28c82d.f4v?key=0c8910dc0caa1c0d115a6dd4c369c8613&src=iqiyi.com&qd_tvid=431333500&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=a1b003077c10ff0737324c5f7eace3ac&qd_sc=f52ea0776a39f4a74efed7309d8580cc&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218113000&qd_vip=1&t=1451218124_4adc1b7fb37d832ef55a5364f3da99cb&cid=afbe8fd3d73448c9&vid=7ed070892a3ac6dcfe01f9130e253116&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431333500_11&ran=204487&uuid=ca6c0ef0-567fd4d4-24',
        # 'http://111.206.23.133/videos/vip/20151224/1c/ba/d3feacb6e33616ce7ae6b275f565c2d8.f4v?key=043f19cdf00f58b979b8be64e7ca77152&src=iqiyi.com&qd_tvid=431333100&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=8f7192098eab8c8ed4f04478bbecbf02&qd_sc=dddf1cae47e0efc4f4eff11457d1843d&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218146000&qd_vip=1&t=1451218143_58d8f847b0100ad7f5242835b6718a2e&cid=afbe8fd3d73448c9&vid=55b6b348078f8e05e9cac28eeb2322bd&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431333100_11&ran=229101&uuid=ca6c0ef0-567fd4eb-57',
        # 'http://111.206.23.142/videos/vip/20151224/57/2b/910d308165ebfefc49961b24db92e336.f4v?key=087719f91f140c761febd2c688ae9a8af&src=iqiyi.com&qd_tvid=431335700&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=8d05c60b621675cc4b6d566d1a6d56ec&qd_sc=08cd4d25a32260e5018da2ee00ba7c64&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218167000&qd_vip=1&t=1451218168_cd34ec3f9511e821909f86701fc7f756&cid=afbe8fd3d73448c9&vid=f1eaa381d9034dc09e2b5ff4cc15c65a&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431335700_11&ran=249122&uuid=ca6c0ef0-567fd4ff-18',
        # 'http://111.206.23.144/videos/vip/20151224/ff/c2/43c50f415275f115390be4e51130f5a9.f4v?key=078ec2a5dfbbdc42da8a6c66e97fa7e8f&src=iqiyi.com&qd_tvid=431334300&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=1a022f82064d6b10c86e2256046b0ac8&qd_sc=2871ab036d29c2505b64de8a27320a3d&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218662000&qd_vip=1&t=1451218692_4e7b28960fbd6d62282b7b87d0cf2d87&cid=afbe8fd3d73448c9&vid=78a7687434f7df0385278846cc62eb8a&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431334300_11&ran=744364&uuid=ca6c0ef0-567fd6ed-18',
        # 'http://111.206.23.143/videos/vip/20151224/30/3d/bcdc65a791c07d2a411965e27eb775ed.f4v?key=05799bc9dd24c67121e4dd72e2fbc8653&src=iqiyi.com&qd_tvid=431337100&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=710024d9440f89740b873ad86e390e5a&qd_sc=0704fed6dcfaf2c176b87dc98da71068&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218681000&qd_vip=1&t=1451218684_0b591a1c570f6af346fcc38be493612a&cid=afbe8fd3d73448c9&vid=9e20aaf635d03ec8ae6a80cf5f51e1c9&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431337100_11&ran=764275&uuid=ca6c0ef0-567fd703-18',
        # 'http://111.206.23.150/videos/vip/20151224/0b/c4/b16523b195cf95b00a543e30eebccf9b.f4v?key=0b77ea6dad7d80bc32100ee168eb8d031&src=iqiyi.com&qd_tvid=431338400&qd_vipres=2&qd_index=1&qd_aid=203166501&qd_start=0&qd_scc=c69d44cc119e3c0b915d3766eb1f2303&qd_sc=30539e5a1692544c4549595d63dc4163&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451218702000&qd_vip=1&t=1451218703_bec66bee017119eaae381c3b3a565993&cid=afbe8fd3d73448c9&vid=1306099bfee6199d73f7ddf1a1f7be9d&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431338400_11&ran=784072&uuid=ca6c0ef0-567fd716-18',

        # 'http://111.206.23.150/videos/vip/20151218/d0/6d/356ab8ce9e296908d5d0d6699a2b80a0.f4v?key=058257b139c02c9bd5cf49eb6924e701c&src=iqiyi.com&qd_tvid=428957200&qd_vipres=2&qd_index=1&qd_aid=428957200&qd_start=0&qd_scc=2366578de9e0d8a48423daec36d5b761&qd_sc=4f1560b1952894036b97ac19679f0827&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451219195000&qd_vip=1&t=1451219197_2e86baaab9d3afebf70d8396ab2e8f27&cid=afbe8fd3d73448c9&vid=466f738ab57aae7029d950192643c8d9&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=428957200_11&ran=855&uuid=ca6c0ef0-567fd904-24',
        # 'http://111.206.23.139/videos/vip/20151118/8a/f5/8eeabdee54295fca8f3a94900ab41d63.f4v?key=08bc22aa3b30966811ef1e0c9badcefeb&src=iqiyi.com&qd_tvid=419691100&qd_vipres=2&qd_index=1&qd_aid=419691100&qd_start=0&qd_scc=c6565b5b546930a65748a24003c982ba&qd_sc=65792b4d3860bfc83d1740eb913968d0&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451219221000&qd_vip=1&t=1451219233_5d9b9459978003125b951b06707538fe&cid=afbe8fd3d73448c9&vid=fc17f368f3da8a19a223d90a1cd72753&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=419691100_11&ran=1000&uuid=ca6c0ef0-567fd926-24'

        # 'http://111.206.23.138/videos/vip/20151225/7c/a0/3fdbdf42c232cef12f804a687b9a6fbe.f4v?key=0bb959cd80046c7deb74538441a89516a&src=iqiyi.com&qd_tvid=430420700&qd_vipres=2&qd_index=1&qd_aid=202842701&qd_start=0&qd_scc=da28899233fe701231c2d2fc757955d1&qd_sc=2d6ca42e5ad7cd2199a440da165d705b&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451219545000&qd_vip=1&t=1451219539_b7e54259a6a2ad9b122e7956bbd3383b&cid=afbe8fd3d73448c9&vid=b823c574a910f0f51ed04c73e8583078&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=430420700_11&ran=1202&uuid=ca6c0ef0-567fda62-24',
        # 'http://111.206.23.131/videos/vip/20151215/87/98/fb5eda512c5e387d8df1e79ceb2ecd15.f4v?key=087742f7876c2882d43a33f5d5a3f5d64&src=iqiyi.com&qd_tvid=430413200&qd_vipres=2&qd_index=1&qd_aid=202842701&qd_start=0&qd_scc=fda43a7bde5c628178302f1967f2e729&qd_sc=576f6fed63e1c29fd4b78289a600eb62&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451219576000&qd_vip=1&t=1451219578_b94f68397c3c199aaa67efc1e5e605f8&cid=afbe8fd3d73448c9&vid=b7e3bb66ec624af2bbb78109ee0a1987&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=430413200_11&ran=30755&uuid=ca6c0ef0-567fda7e-24',
        # 'http://111.206.23.147/videos/vip/20151215/56/bc/3b56f9d720155b30b43b4fc5e406c2ec.f4v?key=0047e6b380a55f25612e3602438b307f3&src=iqiyi.com&qd_tvid=430395300&qd_vipres=2&qd_index=1&qd_aid=202842701&qd_start=0&qd_scc=df27cf547248729fcf73526d7ca4bea8&qd_sc=0ee7dd15ce7e442eccff1fa311f3ddde&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451219583000&qd_vip=1&t=1451219593_12466645941b4a93229096592c6e38d9&cid=afbe8fd3d73448c9&vid=94f0cbd31de057ac44afd01038cfbceb&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=430395300_11&ran=47605&uuid=ca6c0ef0-567fda90-24'
        # 十月初五的月光
        # 'http://111.206.23.141/videos/vip/20151207/76/71/fd481d99ee4fde65bb3dc6ce89b5cf51.f4v?key=0a413362295b32ddf2dbd7a2502804072&src=iqiyi.com&qd_tvid=425395100&qd_vipres=2&qd_index=1&qd_aid=425395100&qd_start=0&qd_scc=b901ab272191429fe4cc440f7ce3d137&qd_sc=9c22a6f8a9a36133d2f48d9b5e18d8a2&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451215638000&qd_vip=1&t=1451215636_7f07e5009213aa66450fb5085ab5e6ac&cid=afbe8fd3d73448c9&vid=0bef46cd9b77cb4bc29b30849d83f662&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=425395100_11&ran=999&uuid=ca6c0ef0-567fcbc4-24'

        # 'http://111.206.23.143/videos/vip/20150805/40/a7/f480e2b41ebbbee3e7577db497a925e4.f4v?key=0de690130566ca35b31195e44f5f36526&src=iqiyi.com&qd_tvid=385580500&qd_vipres=2&qd_index=1&qd_aid=385580500&qd_start=0&qd_scc=ee99364037770cb4fef10473f8200fd7&qd_sc=b6fb6baee67c5198829b0efa80c0992c&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451360566000&qd_vip=1&t=1451360569_05018bb61530df8aa7266174e07ef5b9&cid=afbe8fd3d73448c9&vid=b7276c17174267d5134c0be6482b22ae&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=385580500_11&ran=1324&uuid=ca6c0ef0-56820141-39'

        # 'http://111.206.23.131/videos/vip/20151029/3b/d3/3f7d95f6cb781fdabd284bc515335ad7.f4v?key=032358a2d3aeb8a9787df97e1fd3f0828&src=iqiyi.com&qd_tvid=411189500&qd_vipres=2&qd_index=1&qd_aid=411189500&qd_start=0&qd_scc=52f12cff892982b6bae26ee137223ad3&qd_sc=9027096d0549c1838d571a7c8d5d1cc9&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451360814000&qd_vip=1&t=1451360817_7c1c4647045d8ba651808d57cad4c121&cid=afbe8fd3d73448c9&vid=52b8629e046d549a77ba4f2f10bb8caf&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=411189500_11&ran=1136&uuid=ca6c0ef0-5682023d-39'

        # 'http://111.206.23.140/videos/vip/20150916/e5/56/660507bc69ef3dce60267a80d901bb25.f4v?key=07383def03f77075aedae1855b7727ca7&src=iqiyi.com&qd_tvid=398436000&qd_vipres=2&qd_index=1&qd_aid=398436000&qd_start=0&qd_scc=4cb1d2fabb310d3a1720ab868965c434&qd_sc=7239752e74487e5bf17093a31de719f8&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451361044000&qd_vip=1&t=1451361048_d82e4875046fcb9e01ece52ea76102ab&cid=afbe8fd3d73448c9&vid=6c448d7acd9c5ad2ff9906aba8d42f73&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=398436000_11&ran=1852&uuid=ca6c0ef0-56820323-18'

        # 'http://111.206.23.145/videos/vip/20150930/e8/7b/e350fa0668d7590b2199b6b8cbac7705.f4v?key=0f51c9926b2c0a047d1b4eeb928ef2574&src=iqiyi.com&qd_tvid=399717900&qd_vipres=2&qd_index=1&qd_aid=202550601&qd_start=0&qd_scc=c2c58c7079fe7ea0f132a9bc476c6648&qd_sc=c66efed05fb73824e646be9ed2cd14bc&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451361248000&qd_vip=1&t=1451361251_6a437247f8d74bbaf6424cedea2e1444&cid=afbe8fd3d73448c9&vid=77606d31c61650cbfac09e1ee8f6c350&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=399717900_11&ran=1386&uuid=ca6c0ef0-568203ef-18',
        # 'http://111.206.23.141/videos/vip/20150924/ae/0d/ec5ac1be5441ab8b5b6ba5281363c38d.f4v?key=070cd72467c3775fc8d2f028cf4578d8e&src=iqiyi.com&qd_tvid=399725000&qd_vipres=2&qd_index=1&qd_aid=202550601&qd_start=0&qd_scc=91318bfc1a812e946b355b0d3edb6723&qd_sc=8ce4ba97731282da50b84ebc724ea4f0&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451361282000&qd_vip=1&t=1451361283_1912ac06d7ff93300037704f7799c150&cid=afbe8fd3d73448c9&vid=a945336910d634095a82475e75f91fcc&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=399725000_11&ran=33678&uuid=ca6c0ef0-56820408-18',
        # 'http://111.206.23.133/videos/vip/20150930/5c/48/3f62bd3497266d4bdf0e464f97e9108a.f4v?key=0e25a0c0aabe67eefd6ea8dc4d76836b7&src=iqiyi.com&qd_tvid=399728400&qd_vipres=2&qd_index=1&qd_aid=202550601&qd_start=0&qd_scc=69985502ba76ea76af64d153ffc97e10&qd_sc=2857fb9fdf09a8de0887f5b713aabde1&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1451361294000&qd_vip=1&t=1451361296_04b27c0acb01ee86b1ad9121cf991b45&cid=afbe8fd3d73448c9&vid=9e729c24dd4da4b183d0e44921681257&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=399728400_11&ran=46653&uuid=ca6c0ef0-56820419-18'

        # 'http://111.206.23.137/videos/vip/20151112/1c/92/47914ac41ac5e73ff603ddfd6f891861.f4v?key=0b53d7c9356fe07d987975a2cc279dd40&src=iqiyi.com&qd_tvid=417239000&qd_vipres=2&qd_index=1&qd_aid=417239000&qd_stert=0&qd_scc=8cea34ff8ea97727b989486d9ec71c9d&qd_sc=e1a7a5b2a820d93b89e2634e6dff3834&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453373873000&qd_vip=1&t=1453373876_5b59e4963b8291e0c545eb83ab04d4f5&cid=afbe8fd3d73448c9&vid=cb860c62e70b762dd8715c2621c65acd&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=417239000_11&ran=1563&uuid=ca6c0ef0-56a0b9b5-19&range=0-94888712&qypid=417239000_01010011010000000000_5&ran=2113'
        # 'http://111.206.23.131/videos/vip/20160107/b8/a3/5cf1035b4bf64a53cfd4370699b21df9.f4v?key=0a52a9ef2311f77fae9da104574424c82&src=iqiyi.com&qd_tvid=436323200&qd_vipres=2&qd_index=1&qd_aid=436323200&qd_stert=0&qd_scc=89e51569c4161f20b3167b128806b9c4&qd_sc=df696bf71f4131af040595c3e1b47874&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374237000&qd_vip=1&t=1453374241_a9b7a3074f90c73afeceae6e1b37ad55&cid=afbe8fd3d73448c9&vid=f7b15db90fb9ba4cf64feb4153710656&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=436323200_11&ran=1281&uuid=ca6c0ef0-56a0bb22-19&range=0-59290125&qypid=436323200_01010011010000000000_5&ran=1921',
        # 'http://111.206.23.130/videos/vip/20151102/ee/e1/e492008cf4d68b884282357569a6025b.f4v?key=0d5e83cab8eafbf8db9c70af6a8575f3d&src=iqiyi.com&qd_tvid=412092300&qd_vipres=2&qd_index=1&qd_aid=412092300&qd_stert=0&qd_scc=1ef28b95f1778044b2d94aac7f6ec467&qd_sc=b9d5e9f7c66e0d69ca8075a7b33de90e&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374291000&qd_vip=1&t=1453374295_1d26375bb39adb2c2a58d5111949fe41&cid=afbe8fd3d73448c9&vid=0d311e1d840726d0ad8ffbf783e973b4&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=412092300_11&ran=1398&uuid=ca6c0ef0-56a0bb57-19&range=0-66322431&qypid=412092300_01010011010000000000_5&ran=1746'
        # 'http://111.206.23.150/videos/vip/20151219/90/31/5fa7df93582aa1d9805cbd314ffc4631.f4v?key=0e23c3e79af9a557d3f17db8d2da6beb4&src=iqiyi.com&qd_tvid=429912600&qd_vipres=2&qd_index=1&qd_aid=429912600&qd_stert=0&qd_scc=55dafb16c4cb27b32c79c8646656c7f7&qd_sc=373e719916252594ff5cf7eaa76bebc7&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374347000&qd_vip=1&t=1453374350_9d40e5af227265d7568e4a87898f7672&cid=afbe8fd3d73448c9&vid=6935ba25b461f539949b32f25f3256e9&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=429912600_11&ran=1226&uuid=ca6c0ef0-56a0bb8f-39&range=0-58917536&qypid=429912600_01010011010000000000_5&ran=1590'
        # 'http://111.206.23.146/videos/vip/20151117/43/36/fb60c20c408a8749d53ea28ca21aa774.f4v?key=00636dc0e05c2e0c23cdd43acb9708e1a&src=iqiyi.com&qd_tvid=414349200&qd_vipres=2&qd_index=1&qd_aid=414349200&qd_stert=0&qd_scc=2a21405669f470fd0dad8de3b38754f1&qd_sc=507a8388505bc89eb23bab2276044774&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374402000&qd_vip=1&t=1453374407_b0db6fb2af91eb5ad6f28240cd695164&cid=afbe8fd3d73448c9&vid=79c11efc6870ca89be548efc7d513edf&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=414349200_11&ran=2042&uuid=ca6c0ef0-56a0bbc8-39&range=0-44564479&qypid=414349200_01010011010000000000_5&ran=2786'
        # 'http://111.206.23.150/videos/vip/20151118/9b/1e/331f7166fd9cc0a70c2fe1bf5746a41d.f4v?key=0710fba6b29a04fe22dcb378f9f5ab7e8&src=iqiyi.com&qd_tvid=419743500&qd_vipres=2&qd_index=1&qd_aid=419743500&qd_stert=0&qd_scc=14f787a58af372caee24d97725356b7e&qd_sc=db8e304919f98e14029ee9037eb51546&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374492000&qd_vip=1&t=1453374496_a15efe1681cdd020e2a9324470e8ff40&cid=afbe8fd3d73448c9&vid=7e7b32ff2a3f1998126f7b75ee755923&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=419743500_11&ran=2223&uuid=ca6c0ef0-56a0bc20-39&range=0-59204036&qypid=419743500_01010011010000000000_5&ran=2467'
        # 'http://111.206.23.134/videos/vip/20151224/c0/c7/5eb7d0f877198f897a4c18fbef0503ac.f4v?key=05b157a0ec8c041f8cc0cebff0996b4ee&src=iqiyi.com&qd_tvid=414345000&qd_vipres=2&qd_index=1&qd_aid=414345000&qd_stert=0&qd_scc=249b9fe3238cce2e3f6289e53ae4dc51&qd_sc=a468a057440c89a439b00d219ddf3dfc&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374602000&qd_vip=1&t=1453374606_e9ecf28c5eb55a3829b8f5cd292f2b55&cid=afbe8fd3d73448c9&vid=bf6a0088132ebe3ffe62713a2c724d61&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=414345000_11&ran=2262&uuid=ca6c0ef0-56a0bc8f-38&range=0-35974357&qypid=414345000_01010011010000000000_5&ran=2555'
        # 'http://111.206.23.136/videos/vip/20151111/23/07/9eaef17655041fc1aae58d27103b1b0c.f4v?key=06c5736a46e2d0c98ef2d3d3588d294e0&src=iqiyi.com&qd_tvid=416699000&qd_vipres=2&qd_index=1&qd_aid=416699000&qd_stert=0&qd_scc=10bcfb5d290e54fb248a60d4f0a52f40&qd_sc=21f4d7b4ce905d79fc1944936f669446&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374645000&qd_vip=1&t=1453374649_4005e94b77ad7aa1948e4829349e4a40&cid=afbe8fd3d73448c9&vid=845de7309b7df47f7547b24e2cd7cfc4&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=416699000_11&ran=1386&uuid=ca6c0ef0-56a0bcba-57&range=0-73662463&qypid=416699000_01010011010000000000_5&ran=1834'
        # 'http://111.206.23.137/videos/vip/20151215/00/52/fa79eb1f28f55bf94359c9ea83bd3ac3.f4v?key=0f34afaacc48e7c48d9056a6e6733242c&src=iqiyi.com&qd_tvid=430480400&qd_vipres=2&qd_index=1&qd_aid=430480400&qd_stert=0&qd_scc=f1b83bbc864062c6f78b4e6eb1f34662&qd_sc=bd36132d3d57fa12c6d908a68a731679&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374693000&qd_vip=1&t=1453374697_74f56c20a1450c8fd39ad680a6b8f383&cid=afbe8fd3d73448c9&vid=8c2ce879c226cf66d987fd97c6596305&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=430480400_11&ran=1196&uuid=ca6c0ef0-56a0bce9-57&range=0-60895010&qypid=430480400_01010011010000000000_5&ran=1354'
        # 'http://111.206.23.146/videos/vip/20151117/68/c4/1edcc17130566fa720955b407759aef8.f4v?key=00be7406d8555f6035cbf48d534577abc&src=iqiyi.com&qd_tvid=415533400&qd_vipres=2&qd_index=1&qd_aid=415533400&qd_stert=0&qd_scc=a977a74e92d6dbe6760566e4a03d789a&qd_sc=f81e5173209ed8ff8729157bdafe6aae&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374741000&qd_vip=1&t=1453374745_55ef66696b9c4d0444edc2d448d660e9&cid=afbe8fd3d73448c9&vid=1954370d18552e4e100d8f634f5fa3fe&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=415533400_11&ran=1862&uuid=ca6c0ef0-56a0bd1a-57&range=0-39773190&qypid=415533400_01010011010000000000_5&ran=2052'
        # 'http://111.206.23.149/videos/vip/20151218/93/a5/51b7510e539d9c9a1e63e04120284f6c.f4v?key=0bda38b4fed84c40862077530f928e7c4&src=iqiyi.com&qd_tvid=431495400&qd_vipres=2&qd_index=1&qd_aid=431495400&qd_stert=0&qd_scc=c36de533453dc61a8913a6d20e73519c&qd_sc=17c415082127c55a09d80a302a485ab3&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374781000&qd_vip=1&t=1453374784_62227eae40cce133a7174e77c4b127a6&cid=afbe8fd3d73448c9&vid=435010d97c9e07e48cc69a44ff97f4d8&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=431495400_11&ran=900&uuid=ca6c0ef0-56a0bd41-57&range=0-39206418&qypid=431495400_01010011010000000000_5&ran=1676'
        # 'http://111.206.23.134/videos/vip/20160104/b3/7f/5079ae6e47f9975b4b8106e871a8410e.f4v?key=08526cf12fa72d8199ae3cda8d9e0db11&src=iqiyi.com&qd_tvid=433800200&qd_vipres=2&qd_index=1&qd_aid=433800200&qd_stert=0&qd_scc=643a2a07105a5ef2e4c847384a6da5d1&qd_sc=2790065fe2e57260f8dc3cc32bad587d&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453374827000&qd_vip=1&t=1453374831_e46ffeeeedc552ad10cf2e34e676c6d8&cid=afbe8fd3d73448c9&vid=5cf0c1d571add91cc722287e9df0a828&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=433800200_11&ran=1560&uuid=ca6c0ef0-56a0bd70-57&range=0-46697656&qypid=433800200_01010011010000000000_5&ran=1948'

        # 'http://111.206.23.150/videos/vip/20160120/68/09/1245d6bc9ddb7eef540152ddd5be6f84.f4v?key=0373c1d531a773206b33d8954dcffee21&src=iqiyi.com&qd_tvid=442447600&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=b9401281c1bffbc4c82f5ec1a8621267&qd_sc=17688ddec4b0fef8a0edd465f09e2db1&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705689000&qd_vip=1&t=1453705691_828ae7c053d413430c2058e2af618f34&cid=afbe8fd3d73448c9&vid=1d0cb6395dc96f995ed5bb9f690fc356&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442447600_11&ran=845&uuid=ca6c0ef0-56a5c9db-25&range=0-85721087&qypid=442447600_01010011010000000000_5&ran=1045',
        # 'http://111.206.23.139/videos/vip/20160120/84/ef/20d434933615b77bfd80a11939083738.f4v?key=0711563e6438d2f193dbc69c23079e3c3&src=iqiyi.com&qd_tvid=442448700&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=6b56cc1bf0085f4d839783d53c2ecf2c&qd_sc=ebfa926838ea07844432291afd23e7d7&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705703000&qd_vip=1&t=1453705704_5031ab6885d4d94908e9829a6b6906d3&cid=afbe8fd3d73448c9&vid=b9a8c8fe4e60f69d22d5d1f6c5e6cd14&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442448700_11&ran=14734&uuid=ca6c0ef0-56a5c9e9-25&range=0-81526783&qypid=442448700_01010011010000000000_5&ran=15019',
        # 'http://111.206.23.147/videos/vip/20160120/2f/52/49693230a430db97da57549cf33c3247.f4v?key=048dbd8c4ecf9d4961845a5f3ade663ef&src=iqiyi.com&qd_tvid=442449200&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=a99eab4111a819a1e8c46376c4f80db0&qd_sc=976946e444ff70c3e9efc1ec7f4294c4&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705718000&qd_vip=1&t=1453705719_61eb664af8a293943f6b1b561faee549&cid=afbe8fd3d73448c9&vid=0397e0742937131d819b5ad81f990d62&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442449200_11&ran=29042&uuid=ca6c0ef0-56a5c9f7-25&range=0-69730303&qypid=442449200_01010011010000000000_5&ran=29308',
        # 'http://111.206.23.139/videos/vip/20160120/9f/43/606ccfa9627fd59f074c05e22c38757e.f4v?key=0a3b28ecd23b7fabdd9bf5d623c6bf96f&src=iqiyi.com&qd_tvid=442450300&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=b5c5473bce550e0d3adec44deee404c2&qd_sc=7baa46939e0d0cd7b5d6ec8a8cceabc5&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705758000&qd_vip=1&t=1453705760_123992f84b4868de2ad2ff0703158179&cid=afbe8fd3d73448c9&vid=bcd72229318e8164db3a9f5c83443dd8&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442450300_11&ran=69849&uuid=ca6c0ef0-56a5ca20-25&range=0-74186751&qypid=442450300_01010011010000000000_5&ran=70147',
        # 'http://111.206.23.131/videos/vip/20160120/13/51/1418be4abed8066dac400929b3b4efe5.f4v?key=04355fe86c7c83d32f4bfb9a3d98afc2f&src=iqiyi.com&qd_tvid=442451500&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=c3d91665ff6fbeea2ff5d2c040df3158&qd_sc=2da000b4e0b2ca3340c29c7bbae9fd4b&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705778000&qd_vip=1&t=1453705779_b4885a9e9929e55d9701e4eb733481d4&cid=afbe8fd3d73448c9&vid=1623f6771b7ebb540310d6b728fbab14&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442451500_11&ran=89903&uuid=ca6c0ef0-56a5ca34-19&range=0-73138175&qypid=442451500_01010011010000000000_5&ran=90435',
        # 'http://111.206.23.150/videos/vip/20160120/f3/6b/40704bacf85679e01281b65f01a626bc.f4v?key=06d148bfee3a089955fdc0d755b7138b4&src=iqiyi.com&qd_tvid=442454100&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=ec9629f425ba5d1bc43c18c41f1237cf&qd_sc=e879fa9f3ff43fce7f3b52c1fed08010&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705790000&qd_vip=1&t=1453705791_1f6ce108393d1764866965d3da707ac4&cid=afbe8fd3d73448c9&vid=58909848d8233cdcdea5d21803d67525&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442454100_11&ran=101493&uuid=ca6c0ef0-56a5ca40-8d&range=0-73662463&qypid=442454100_01010011010000000000_5&ran=101841',
        # 'http://111.206.23.144/videos/vip/20160120/eb/a7/afdf1480d6aecb631bb4cbe68f35495d.f4v?key=0e6fb325f68622dedefdcdafc0500bbd7&src=iqiyi.com&qd_tvid=442455200&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=20eebd9d55439da8c1cc6e2b9f245182&qd_sc=fb45aaf704aa4023e4ef531ed4923bb8&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705816000&qd_vip=1&t=1453705818_c2637f7ea10d0b0f5055d4eb0b371570&cid=afbe8fd3d73448c9&vid=a0a08864e3a2a632d4ce731feee7fd2d&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442455200_11&ran=127914&uuid=ca6c0ef0-56a5ca5a-8d&range=0-79953919&qypid=442455200_01010011010000000000_5&ran=128199',
        # 'http://111.206.23.142/videos/vip/20160120/67/e8/019f01ed5721454f8409b48f8c5f53bf.f4v?key=04a6d0556c732cdb8e14a3a2f58b565be&src=iqiyi.com&qd_tvid=442456100&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=c12329c28aa92f0de94711e2559912c4&qd_sc=02eb7e2d3c67852f108d5832f29c7dee&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705833000&qd_vip=1&t=1453705835_9b952e463c9d51b3dcf0372f17b862f4&cid=afbe8fd3d73448c9&vid=d0b2e2fad76110284115f8490dcba3a0&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442456100_11&ran=145246&uuid=ca6c0ef0-56a5ca6b-8d&range=0-78643199&qypid=442456100_01010011010000000000_5&ran=145620',
        # 'http://111.206.23.136/videos/vip/20160120/d7/bf/2d2f89d7d50006c0f137db7eee9321e6.f4v?key=0969ac3ec1aa777cae4515cb5d5de8f73&src=iqiyi.com&qd_tvid=442457500&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=cbdd7ef7da1881b881b400a2fb46e7cb&qd_sc=b21a9032582ccb71591816d584ad9f36&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705847000&qd_vip=1&t=1453705848_9d1d4915fe0dd58a1ff15a17c387a2b9&cid=afbe8fd3d73448c9&vid=7a044e02ef19f5c80fcb1a0d65a61d42&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442457500_11&ran=158960&uuid=ca6c0ef0-56a5ca79-8d&range=0-74711039&qypid=442457500_01010011010000000000_5&ran=159295',
        # 'http://111.206.23.134/videos/vip/20160120/fe/40/3f650218df638ac70cc168de140ed49f.f4v?key=003cdd1a888ee9e7fa914d3788ab0325&src=iqiyi.com&qd_tvid=442460400&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=5f56c543945b73b8b8debfc01ac200ff&qd_sc=a0e3b33f13129c3c7c329a79d8f9e903&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453705999000&qd_vip=1&t=1453706000_16008dca8cb51ce1daf8fcf1080b0978&cid=afbe8fd3d73448c9&vid=467ba066f1f3197e29ff600ebc6e0dab&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=442460400_11&ran=310407&uuid=ca6c0ef0-56a5cb10-8d&range=0-64225279&qypid=442460400_01010011010000000000_5&ran=311806',
        # 'http://111.206.23.140/videos/vip/20160120/3d/6f/d82803768121f2a1f39984151d475b24.f4v?key=055bd42cbc615188dbbd489dbd6645f8&src=iqiyi.com&qd_tvid=443299600&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=85d3012cbeba459e20b9e875cc65cacb&qd_sc=013777729b8cd525a9a3dd6048740d1b&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453706181000&qd_vip=1&t=1453706183_459e57ec001a1038df88cd5e9f8be396&cid=afbe8fd3d73448c9&vid=d4f888521814fbf69004751f8df89e9c&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443299600_11&ran=493265&uuid=ca6c0ef0-56a5cbc7-18&range=0-70778879&qypid=443299600_01010011010000000000_5&ran=494498',
        # 'http://111.206.23.145/videos/vip/20160120/71/33/d499a0d7101947965fc18de54e95d878.f4v?key=089db7ef1ee0926a61ed65f0f2b18a5b3&src=iqiyi.com&qd_tvid=443300000&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=5799df9aa4c4bef35c01926226080ad6&qd_sc=12005937de65d9a3c2b8b13990c6f8eb&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453706200000&qd_vip=1&t=1453706202_7283375e3c6ff68beb2b3afaea0435a4&cid=afbe8fd3d73448c9&vid=90529af11840fdbe3fbe4f9497c28bf1&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443300000_11&ran=511968&uuid=ca6c0ef0-56a5cbda-19&range=0-77856767&qypid=443300000_01010011010000000000_5&ran=512466',
        # 'http://111.206.23.141/videos/vip/20160120/cf/9c/ed3fff442d9b6239a96b93c2e95c5fb5.f4v?key=03a533d732687cf134f4c5d5e8139a978&src=iqiyi.com&qd_tvid=443300300&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=18da46fd81ee80edf0c37026ba2fd4da&qd_sc=fa1074c278bfc40df06f57f0a4860743&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453706218000&qd_vip=1&t=1453706220_9ee12f965b88db97c92cb4467276436f&cid=afbe8fd3d73448c9&vid=5b61ea81d0fed9e55636d5b81dcbe794&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443300300_11&ran=530712&uuid=ca6c0ef0-56a5cbed-19&range=0-73138175&qypid=443300300_01010011010000000000_5&ran=530949',
        # 'http://111.206.23.133/videos/vip/20160120/64/31/c5174241146e4b4ebfea3d5b79751527.f4v?key=0d5faba330e28bd2551a0c7ea28439910&src=iqiyi.com&qd_tvid=443300700&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=fb461c7a295da391a23017993a552365&qd_sc=9a1214faefbb9269073341280fdc429c&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453709601000&qd_vip=1&t=1453709602_f3a330e2918068e1a6846c76ba7bb96b&cid=afbe8fd3d73448c9&vid=627969b2ce813d45fbefe2fe826baa64&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443300700_11&ran=780204&uuid=ca6c0ef0-56a5d922-8a&range=1835008-2621439&qypid=443300700_01010011010000000000_2&ran=899575'
        # 'http://111.206.23.143/videos/vip/20160120/c6/74/452bcdaf90317a88725c61ca1277ba1c.f4v?key=07be3582945e90b5656ab65b8aa7a1c88&src=iqiyi.com&qd_tvid=443301100&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=897a35ee95caf8379474363d77d81f4b&qd_sc=52ce44a0bdb6dd5c38078a071211e663&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453706262000&qd_vip=1&t=1453706264_f79fe8fe3dac8e9e458d515e4c4af606&cid=afbe8fd3d73448c9&vid=a1d00fbc0505fd98ded1feafbe12a8d8&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443301100_11&ran=574290&uuid=ca6c0ef0-56a5cc19-19&range=0-80478207&qypid=443301100_01010011010000000000_5&ran=574741',
        # 'http://111.206.23.135/videos/vip/20160120/1c/18/3dea25d2c4c57382cf4949c7cf9f7e70.f4v?key=0b8ae0416a3ed5e38c05c2a9e4b1a7a8c&src=iqiyi.com&qd_tvid=443301500&qd_vipres=2&qd_index=1&qd_aid=203166601&qd_stert=0&qd_scc=3d3b8e0f392dabd89d0943fdc1066b92&qd_sc=9a9643a6800e8ab2cc1c5c0a19f9bae1&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1453706277000&qd_vip=1&t=1453706279_bca80e9676a89e2fc8977c3e5e59bc5a&cid=afbe8fd3d73448c9&vid=accb151af352a92e28534e743ced7d5c&QY00001=2047395208&qyid=zapwmqcgibxtwhqmhphh2zp5dkdsopbp&qypid=443301500_11&ran=589074&uuid=ca6c0ef0-56a5cc27-19&range=0-79167487&qypid=443301500_01010011010000000000_5&ran=589413',

        # 'http://111.206.23.130/videos/vip/20160224/3b/35/65733bc47667e8b9cadb97de0b2343f3.f4v?key=0bc12854f844320a6ed8deb620369378d&src=iqiyi.com&qd_tvid=453406400&qd_vipres=2&qd_index=1&qd_aid=202938201&qd_stert=0&qd_scc=0ecccef42806ce1135429fc7f5802678&qd_sc=777b1c618dc66b459186a2fc565de7b6&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=ca6c0ef0&qd_uid=2047395208&qd_tm=1456366192000&qd_vip=1&t=1456366198_990e22638905c1b032a1030c6eff9fd6&cid=afbe8fd3d73448c9&vid=7c73a9ed6e02e7e2051bdb81f233d569&QY00001=2047395208&qyid=0c53ccedbbbd7989dafea2c769c944b8&qypid=453406400_11&s=4525099.009900991&bt=163168&z=beijing4_cnc&la=CNC|QiYi-202.108.14.240&li=beijing4_cnc&lsp=-1&lc=48&ran=4459&uuid=ca6c0ef0-56ce6276-39&range=8912896-44564479&qypid=453406400_01010011010000000000_2&ran=6690',
        'http://101.246.186.14/videos/vip/20160225/25/87/49442b4309801b275f03448d77db1815.f4v?key=0e70c5ba50da539d6329057e5da3a5e3&src=iqiyi.com&qd_tvid=453787200&qd_vipres=2&qd_index=1&qd_aid=202938201&qd_stert=0&qd_scc=44ba236df5fde00d7d4df372394ee291&qd_sc=cd1531307040554156f4200e72a5c5e2&qd_src=1702633101b340d8917a69cf8a4b8c7c&qd_ip=e82b298&qd_uid=2047395208&qd_tm=1456406307000&qd_vip=1&t=1456406312_af543cf32b9a898581b7f550e1b8ed8a&cid=afbe8fd3d73448c9&vid=5b9700ec0169e370cda08adf539dddfd&QY00001=2047395208&qyid=80ec72392c754a978362ddeea01f6649&qypid=453787200_11&ran=2255&uuid=e82b298-56ceff29-2c&range=0-8191&qypid=453787200_01010011010000000000_5&ran=3356'


        ]
    video_path = ''
    start_time_max = 0
    album_data = None
    # is_movie = True
    is_movie = False
    # 需要先下载，有延迟失效
    # for url in urls:
    #     # &start=9175040&end=58550527
    #     url = url[0: url.find('&range=')]
    #     index = url.find('&qypid=')+7
    #     tvid = url[index: url.find('_', index)]
    #     video_path = video_base_path+site+'/'+ tvid + '.flv'
    #     if os.path.exists(video_path):
    #         os.remove(video_path)
    #     print tvid
    #     size = HTMLResource(url, headers=headers).download_video(video_path, 1024*1024*200)
    #     print size

    for url in urls:
        # &start=9175040&end=58550527
        url = url[0: url.find('&range=')]
        index = url.find('&qypid=')+7
        tvid = url[index: url.find('_', index)]
        video_path = video_base_path+site+'/'+ tvid + '.flv'
        data = get_data(tvid)
        _id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = data
        update_album_datas('_' + str(album_id), video_title, link, album_id, online_time, 120, tvid)
        print video_title
        if is_movie or start_time < 0:
            start_time = 0
        download_video([tvid, vid, start_time, video_title, link, album_id, online_time, url])
        if start_time > start_time_max:
            start_time_max = start_time
            album_data = data
    if not is_movie and start_time_max > 0:
        _id, doc_id, video_no, tvid, vid, link, video_title,album_id,online_time,start_time = album_data
        download_album_video([tvid, vid, album_id, start_time, video_title, link, online_time, None])