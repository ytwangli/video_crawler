#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from resource.http import JsonResource, XmlResource
from resource.database import DataBase
import datetime
import threadpool
import traceback
from urllib import quote
import time
import sys

class IqiyiData(object):

    def __init__(self):
        self.proxy = None
        self.timeout = 60
        self.page_size = 21
        self.pool_size = 1
        self.headers = {'Referer': 'http://m.iqiyi.com/zongyi/?tjsrc=20131014_2006',
                        'Accept': '*/*',
                        'X-Requested-With': 'com.android.browser',
                        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MI-ONE Plus Build/JZO54K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 XiaoMi/MiuiBrowser/1.0',
                        'Accept-Encoding': 'gzip,deflate',
                        'Accept-Language': 'zh-CN, en-US',
                        'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
                        }

        self.detail_headers = {'Referer': 'http://m.iqiyi.com/v_19rrn6vmvo.html',
                        'Origin': 'http://m.iqiyi.com',
                        'X-Requested-With': 'com.android.browser',
                        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; MI-ONE Plus Build/JZO54K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 XiaoMi/MiuiBrowser/1.0',
                        'Accept-Encoding': 'gzip,deflate',
                        'Accept-Language': 'zh-CN, en-US',
                        'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
                        }

        # pps 电影,电视剧 超过3000-143页, iqiyi 电影超
        # "电影,1;电视剧,2;纪录片,3;动漫,4;音乐,5;综艺,6;娱乐,7;游戏,8;旅游,9;片花,10;公开课,11;教育,12;时尚,13;时尚综艺,14;少儿综艺,15;微电影,16;体育,17;奥运,18;直播,19;广告,20;生活,21;搞笑,22;奇葩,23",
        # 脱口秀31
        self.catagorys = [
            ('movie','电影',1,['','华语','美国','欧洲','韩国','日本','泰国','其它', '动作','喜剧','爱情','惊悚','科幻','恐怖','伦理','悬疑','犯罪','剧情','网络大电影']),
            ('tvplay','电视剧',2,['','内地','韩国','美剧','日本','台湾','香港','泰国', '青春剧','偶像剧','言情剧','古装剧','喜剧','军旅剧','家庭剧','科幻剧','武侠剧','历史剧']),
            ('tvshow','综艺',6,['','内地','港台','日韩','欧美', '爱奇艺出品','真人秀','脱口秀','游戏','访谈','选秀','播报','搞笑','情感','相亲','美食','时尚','曲艺','盛会','少儿','粤语','其它']),
            ('comic','动漫',4,['','大陆','日本','美国','法国','韩国','英国','新西兰','俄罗斯','其它', '0-3','4-6','7-13','14-17','18以上']),
            ('documentary','纪录片',3,['','国内','国外', '探索','历史','军事','社会','文化','人物','自然']),
            ('sport','体育',17,['']),
            ('music','音乐',5,['']),
            ('fun','娱乐',7,['']),
            ('game','游戏',8,['']),
            ('travel','旅游',9,['']),
            ('live','生活',21,['']),
            ('child','少儿',15,['']),
            ('edu','教育',12,['','幼儿','小学', '初中','高中','外语学习','职业教育','管理培训','学历教育','实用教程','公开课']),
            ('micromovie','微电影',16,['','剧情片','动画片','创意','纪录片','音乐']),
            ('fashion','时尚',13,['']),
            ('talkshow','脱口秀',31,['']),
            ('finance','财经',24,['']),
            ('auto','汽车',26,['']),
        ]
        self.video_set = set()  # 已经获取过信息的doc_id
        self.video_list = list()  # 新获取的视频信息
        self.video_detail_set = set()  # 已经获取过的详情子集的doc_id+'-'+tvid+'-'+vid
        self.video_detail_list = list()  # 新获取的详情子集信息

    def clear_all(self):
        # 清空所有
        self.video_set.clear()
        self.video_detail_set.clear()
        del self.video_list[0:len(self.video_list)]
        del self.video_detail_list[0:len(self.video_detail_list)]

    def clear_cache(self):
        # 清空存储
        del self.video_list[0:len(self.video_list)]
        del self.video_detail_list[0:len(self.video_detail_list)]


    def save(self, for_copyright=False):
        detail_table = 'iqiyi_details'
        if for_copyright:
            detail_table = 'iqiyi_copyright_details'
        conn, cur = DataBase.open_conn_qidun()
        count = len(self.video_list)
        print count
        tmp_list = []
        for video in self.video_list:
            tmp_list.append(video)
            count = count - 1
            # 分次保存信息
            if count % 1000 == 0:
                cur.executemany('insert into iqiyi_data(doc_id,qipu_id,album_id,site_id,album_title,album_subtitle,album_alias,'
                    'category,category_id,category_name,album_link,album_image,album_poster,director,actor,lib_link,album_pubdate,'
                    'newest_pubdate,total_number,newest_number,play_count,series,source_id,album_type,is_purchase,is_exclusive,'
                    'is_qiyi_produced,create_date,update_date) '
                    'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', tmp_list)
                conn.commit()
                del tmp_list[0:len(tmp_list)]

        count = len(self.video_detail_list)
        print count
        tmp_list = []
        for video_detail in self.video_detail_list:
            tmp_list.append(video_detail)
            count = count - 1
            # 分次保存信息
            if count % 1000 == 0:
                cur.executemany('insert into '+detail_table+'(doc_id,album_id,video_no,video_title,video_subtitle,'
                    'video_site,link,image,online_time,qipu_id,tvid,vid,time_length,start_time,create_date,update_date) '
                    'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', tmp_list)
                conn.commit()
                del tmp_list[0:len(tmp_list)]
        DataBase.close_conn(conn, cur)


    def crawler(self):
        conn, cur = DataBase.open_conn_qidun()
        cur.execute("SELECT doc_id FROM iqiyi_data")
        for data in cur.fetchall():
            self.video_set.add(data[0])
        #  key = doc_id+'-'+tvid+'-'+vid
        cur.execute("SELECT doc_id, tvid, vid FROM iqiyi_details")
        for data in cur.fetchall():
            key = data[0]+'-'+data[1]+'-'+data[2]
            self.video_detail_set.add(key)
        DataBase.close_conn(conn, cur)

        self.crawler_site('iqiyi')
        self.crawler_site('pps')


    def crawler_site(self, sub_site):
        video_list_paras = []
        for (category, category_name, category_id, category_subnames) in self.catagorys:
            for category_subname in category_subnames:
                pagenum = self.get_video_list_pagenum(category_name, category_subname, sub_site)
                print ('category_name: %s, category_subname: %s, pagenum: %s.' % (category_name, category_subname, pagenum))
                for pageNo in xrange(1, pagenum+1):
                    video_list_paras.append([category, category_id, category_name, pageNo, category_subname, sub_site])
        count = len(video_list_paras)
        print count

        tmp_paras = []
        for para in video_list_paras:
            tmp_paras.append(para)
            count -= 1
            if count % 100 == 0:
                print count

                # 每次多线程获取100个列表页面
                pool = threadpool.ThreadPool(self.pool_size)
                requests = threadpool.makeRequests(self.get_video_list, tmp_paras)
                [pool.putRequest(req) for req in requests]
                pool.wait()
                pool.dismissWorkers(self.pool_size, do_join=True)

                del tmp_paras[0:len(tmp_paras)]
                self.save()
                self.clear_cache()

    def get_video_list_pagenum(self, category_name, category_subname, sub_site):
        pageNum = 1
        try:
            if category_subname != '':
                category_subname = '%s;must' % (category_subname)
            url = 'http://search.video.qiyi.com/o?pageNum=%s&mode=4&ctgName=%s&threeCategory=%s&pageSize=%s' \
                  '&type=list&if=html5&pos=1&site=%s&callback=window.Q.__callbacks__.cbbasrf1&access_play_control_platform=15&qyid=92f7f5cfdfd2b83bc872634fefe8af5e' \
                % (pageNum, quote(category_name), quote(category_subname), self.page_size, sub_site)
            content = JsonResource(url, self.headers, proxies=self.proxy).get_resource()
            if content is not None:
                totalNum = content.get('result_num', 1)
                totalPageNum = (totalNum-1)/self.page_size + 1
                return int(totalPageNum)
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('pageNum:%s, category_name:%s result exception.' % (pageNum, category_name))
        return 0


    def get_video_list(self, para):
        category, category_id, category_name, pageNum, category_subname, sub_site = para
        exe_time = datetime.datetime.now()
        try:
            if category_subname != '':
                category_subname = '%s;must' % (category_subname)
            url = 'http://search.video.qiyi.com/o?pageNum=%s&mode=4&ctgName=%s&threeCategory=%s&pageSize=%s' \
                  '&type=list&if=html5&pos=1&site=%s&callback=window.Q.__callbacks__.cbbasrf1&access_play_control_platform=15&qyid=92f7f5cfdfd2b83bc872634fefe8af5e' \
                % (pageNum, quote(category_name), quote(category_subname), self.page_size, sub_site)
            content = JsonResource(url, self.headers, proxies=self.proxy).get_resource()
            if content is not None:  # and 'data' in content and content['data'] != ' search result is empty ' and content['code'] == 'A00000'
                videos = content.get('docinfos', [])
                if len(videos) == 0:
                    if int(pageNum) == 1:
                        print 'Error:'
                        print url

                for video in videos:
                    try:
                        if 'doc_id' not in video or video['doc_id'] == '':
                            continue
                        doc_id = video['doc_id']
                        video_id = doc_id
                        video_data = video.get('albumDocInfo')
                        if 'siteId' not in video_data:
                            continue
                        site_id = video_data.get('siteId', '')
                        if site_id != 'iqiyi' and site_id != 'pps':
                            continue
                        video_lib_meta = video_data.get('video_lib_meta')
                        if video_id not in self.video_set:
                            self.video_set.add(video_id)
                            qipu_id = str(video_data.get('qipu_id', ''))
                            albumId = str(video_data.get('albumId', ''))
                            albumTitle = video_data.get('albumTitle', '')
                            albumAlias = video_data.get('albumAlias', '')
                            alias = video_lib_meta.get('alias', '')
                            albumLink = video_data.get('albumLink', '')
                            albumImg = video_data.get('albumImg', '')
                            poster = video_lib_meta.get('poster', '')
                            director = video_data.get('director', '')
                            star = video_data.get('star', '')
                            lib_link = video_lib_meta.get('link', '')  # 影视大全的link
                            releaseDate = video_data.get('releaseDate', '')
                            latest_update_time = video_data.get('latest_update_time', '')
                            itemTotalNumber = video_data.get('itemTotalNumber', video_lib_meta.get('total_video_count', 1))
                            newest_item_number = video_data.get('newest_item_number', '')
                            playCount = video_data.get('playCount', '')
                            series = video_data.get('series', False)
                            source_id = video_data.get('sourceCode', '')
                            album_type = int(video_data.get('album_type', -1))  # -1 电影, 0 电视剧, 1 综艺
                            is_purchase = video_data.get('isPurchase', False)  # 0 vip: 1 2
                            if is_purchase != False:
                                is_purchase = True
                            is_exclusive = video_data.get('is_exclusive', False)
                            is_qiyi_produced = video_data.get('is_qiyi_produced', False)
                            video_info = [video_id, qipu_id, albumId, site_id, albumTitle, albumAlias, alias, category, category_id, category_name,
                                        albumLink, albumImg, poster, director, star, lib_link, releaseDate, latest_update_time, itemTotalNumber,
                                        newest_item_number, playCount, series, source_id, album_type, is_purchase, is_exclusive, is_qiyi_produced, exe_time, exe_time]
                            self.video_list.append(video_info)

                            self.get_video_detail_info(exe_time, doc_id, albumId, site_id, video['albumDocInfo']['videoinfos'])
                    except Exception as e:
                        print e
                        traceback.print_exc()
                        logging.info('pageNum:%s, category_id:%s result exception.' % (pageNum, category_id))
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('pageNum:%s, category_id:%s result exception.' % (pageNum, category_id))


    # 列表信息中穿插的单个视频详情
    def get_video_detail_info(self, exe_time, doc_id, albumId, site_id, videoinfos):
        for video in videoinfos:
            tvid = str(video.get('tvId', video.get('itemUploadID', '')))
            vid = video.get('vid', '')
            qipu_id = str(video.get('qipu_id', ''))
            key = doc_id+'-'+tvid+'-'+vid
            if key not in self.video_detail_set:
                self.video_detail_set.add(key)
                itemNumber = str(video.get('year', '1'))
                if len(itemNumber) != 8:  # 综艺
                    itemNumber = video.get('itemNumber', '1')
                itemTitle = video.get('itemTitle', '')
                subTitle = video.get('subTitle', '')
                itemLink = video.get('itemLink', video.get('p2pLink', ''))
                itemHImage = video.get('itemHImage', '')
                online_time = video.get('initialIssueTime', '')
                timeLength = video.get('timeLength', '')
                self.video_detail_list.append([doc_id, albumId, itemNumber, itemTitle, subTitle, site_id, itemLink,
                                itemHImage, online_time, qipu_id, tvid, vid, timeLength, 0, exe_time, exe_time])


    # 获取版权剧集的详情信息
    def crawler_copyright(self):
        conn, cur = DataBase.open_conn_qidun()
        copyright_qipu_ids = []
        copyright_videos = []

        cur.execute("SELECT qipu_id FROM copyright_videos where monitor = 1;")
        for data in cur.fetchall():
            # self.video_set.add(data[0])
            copyright_qipu_ids.append(data[0])
        cur.execute("SELECT doc_id,qipu_id,album_type,total_number,category_id,source_id,album_id,site_id FROM iqiyi_data WHERE qipu_id in (%s);" % (','.join(copyright_qipu_ids)) )
        for data in cur.fetchall():
            copyright_videos.append(data)
        print len(copyright_qipu_ids)
        print len(copyright_videos)

        #  key = doc_id+'-'+tvid+'-'+vid
        cur.execute("SELECT doc_id, tvid, vid FROM iqiyi_copyright_details;")
        for data in cur.fetchall():
            key = data[0]+'-'+data[1]+'-'+data[2]
            self.video_detail_set.add(key)
        DataBase.close_conn(conn, cur)

        for video in copyright_videos:
            doc_id, qipu_id, album_type, total_number, category_id, source_id, album_id, site_id = video
            if album_type == -1 and total_number != '1':  # 部分电视剧、综艺没有album_type标签，默认为-1了
                yyyydd_list = self.get_zongyi_detail_years(category_id, source_id)
                if len(yyyydd_list) == 0:
                    album_type = 0  # 电视剧
                else:
                    album_type = 1  # 综艺

            if album_type == 0:  # 电视剧
                self.get_dianshiju_details(category_id, doc_id, album_id, site_id)
            elif album_type == 1:  # 综艺
                self.get_zongyi_details(category_id, doc_id, album_id, site_id, source_id)
            elif album_type == -1:  # 电影
                print video
                # 电影由后面函数从detail库搜索引入
        self.save(True)
        self.clear_cache()


    # 电视剧
    def get_dianshiju_details(self, category_id, doc_id, album_id, site_id):
        page_num = 1
        total_page_num = self.get_dianshiju_detail(category_id, doc_id, page_num, album_id, site_id)
        # 不会太多页，无需多线程
        if total_page_num > 1:
            for pageDetailNum in range(2, total_page_num+1):
                self.get_dianshiju_detail(category_id, doc_id, page_num, album_id, site_id)


    def get_dianshiju_detail(self, category_id, doc_id, page_num, album_id, site_id):
        total_page_num = 1
        exe_time = datetime.datetime.now()
        try:
            url = 'http://cache.video.iqiyi.com/avlist/%s/%s/?callback=jsonp12' % (album_id, page_num)
            content = JsonResource(url, self.detail_headers, proxies=self.proxy).get_resource()
            if content is not None and 'data' in content and content['code'] == 'A00000':
                #allNum = content['data']['allNum']
                total_page_num = int(content['data']['pgt'])
                for video in content['data']['vlist']:
                    tvid = str(video['id'])
                    vid = video['vid']
                    if 'publishTime' in video:
                        publishTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(video['publishTime']/1000))
                    else:
                        publishTime = video['tvYear']
                    key = doc_id+'-'+tvid+'-'+vid
                    if key not in self.video_detail_set:
                        self.video_detail_set.add(key)
                        start_time, qipu_id = self.get_detail_start_time(tvid, vid)
                        video_detail = [doc_id, album_id, video['pds'], video['vn'], video['vt'], site_id, video['vurl'],
                                        video['vpic'], publishTime, qipu_id, tvid, vid, video['timeLength'], start_time, exe_time, exe_time]
                        self.video_detail_list.append(video_detail)
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('page_num:%s, category_id:%s, album_id:%s result exception.' % (page_num, category_id, album_id))
        return total_page_num

    def get_detail_start_time(self, tvid, vid):
        try:
            url = 'http://cache.video.qiyi.com/jp/vi/%s/%s/?status=1' % (tvid, vid)
            content = JsonResource(url, self.detail_headers, proxies=self.proxy).get_resource()
            if content is not None and 'startTime' in content:
                start_time = int(content['startTime'])
                # end_time = int(content['endTime'])
                qipu_id = content['videoQipuId']
                return start_time, qipu_id
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('tvid:%s, vid:%s start_time result exception.' % (tvid, vid))
        return None, None

    # 综艺
    def get_zongyi_details(self, category_id, doc_id, album_id, site_id, source_id):
        yyyydd_list = self.get_zongyi_detail_years(category_id, source_id)
        tmp_paras = []
        for yyyydd in yyyydd_list:
            tmp_paras.append([category_id, doc_id, album_id, yyyydd, site_id, source_id])

        pool = threadpool.ThreadPool(self.pool_size)
        requests = threadpool.makeRequests(self.get_zongyi_detail, tmp_paras)
        [pool.putRequest(req) for req in requests]
        pool.wait()
        pool.dismissWorkers(self.pool_size, do_join=True)


    # 获取综艺子集列表
    def get_zongyi_detail_years(self, category_id, source_id):
        yyyydd_list = []
        try:
            url = 'http://cache.video.iqiyi.com/sdlst/%s/%s/?callback=jsonp12' % (category_id, source_id)
            content = JsonResource(url, self.detail_headers, proxies=self.proxy).get_resource()
            if content is not None and 'code' in content and content['code'] == 'A00000':
                # allNum = content['count']
                yyyy_dd = content['data']  #dict: key -> list
                for yyyy in yyyy_dd.keys():
                    if int(yyyy) >= 2013:
                        for dd in yyyy_dd[yyyy]:
                            yyyydd_list.append(yyyy+dd)
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('category_id:%s, source_id:%s result exception.' % (category_id, source_id))
        return yyyydd_list


    def get_zongyi_detail(self, para):
        category_id, doc_id, album_id, yyyydd, site_id, source_id = para
        exe_time = datetime.datetime.now()
        try:
            url = 'http://cache.video.iqiyi.com/sdvlst/%s/%s/%s/?callback=jsonp12' % (category_id, source_id, yyyydd)
            content = JsonResource(url, self.detail_headers, proxies=self.proxy).get_resource()
            if content is not None and 'code' in content and content['code'] == 'A00000':
                for video in content['data']:
                    # 部分剧集没有任何数据,仅仅选用vid判断一下
                    if 'vid' not in video:
                        continue
                    tvid = str(video['tvId'])
                    vid = video['vid']
                    publishTime = video['tvYear']
                    if 'publishTime' in video:
                        publishTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(video['publishTime']/1000))
                    key = doc_id+'-'+tvid+'-'+vid
                    if key not in self.video_detail_set:
                        self.video_detail_set.add(key)
                        start_time, qipu_id = self.get_detail_start_time(tvid, vid)
                        video_detail = [doc_id, album_id, yyyydd, video['videoName'], video['tvSbtitle'], site_id, video['vUrl'],
                                        video['tvPicUrl'], publishTime, qipu_id, tvid, vid, video['timeLength'], start_time, exe_time, exe_time]
                        self.video_detail_list.append(video_detail)
            else:
                logging.info('%s result error.' % url)
        except Exception as e:
            print e
            traceback.print_exc()
            logging.info('category_id:%s, source_id:%s, yyyydd:%s result exception.'
                         % (category_id, source_id, yyyydd))


    # # 内网查询接口
    # def get_video_detail_list(self, para):
    #     is_OK = False
    #     site_id = para[0]
    #     doc_id = para[1]
    #     exe_time = datetime.datetime.now()
    #     try:
    #         url = 'http://search.video.qiyi.domain/o?if=video_library&video_library_type=play_source&platform=4&key=%s' % (doc_id)
    #         content = JsonResource(url, self.detail_headers, proxies=self.proxy).get_resource()
    #         if content is not None and 'video_info' in content:
    #             album_id = str(content['album_id'])
    #             #allNum = content['data']['allNum']
    #             for video_detail in content['video_info']:
    #                 if 'tv_id' not in video_detail:
    #                    continue
    #                 tvId = str(video_detail['tv_id'])
    #                 vid = video_detail['v_id']
    #                 qipu_detail_id = str(video_detail['qipu_id'])
    #                 key = doc_id+'-'+qipu_detail_id
    #                 if key not in self.video_detail_set:
    #                     self.video_detail_set.add(key)
    #                     video_info = []
    #                     # album_id,site_id,video_no,video_name,video_subname,video_site,url,image_url,online_time,
    #                     # definition,definition_name,video_url_id,video_url,time_length
    #                     video_info.append(doc_id)
    #                     if 'album_id' in video_detail:
    #                         album_detail_id = str(video_detail['album_id'])
    #                     else:
    #                         album_detail_id = album_id
    #                     video_info.append(album_detail_id)
    #                     video_info.append(site_id)
    #                     video_no = 1
    #                     if 'play_order' in video_detail:
    #                         video_no = video_detail['play_order']
    #                     elif 'year' in video_detail:
    #                          video_no = video_detail['year']
    #                     video_info.append(video_no)
    #                     video_info.append(video_detail['title'])
    #                     video_info.append(video_detail['desciption'])
    #                     video_info.append(site_id)
    #                     video_info.append(video_detail['play_url'])
    #                     video_info.append(video_detail['image_url'])
    #                     video_info.append(None)
    #                     video_info.append(qipu_detail_id)                 # definition - qipu_id
    #                     video_info.append(None)                  # definition_name
    #                     video_info.append(tvId)  # video_url_id
    #                     video_info.append(vid)  # video_url
    #                     video_info.append(content['duration'])
    #                     video_info.append(exe_time)
    #                     video_info.append(exe_time)
    #                     self.video_detail_list.append(video_info)
    #                     is_OK = True
    #         else:
    #             logging.info('%s result error.' % url)weibo_url
    #     except Exception as e:
    #         print e
    #         traceback.print_exc()
    #         logging.info('doc_id:%s result exception.' % (doc_id))
    #     return is_OK



    # 将iqiyi_details中的版权电影（非剧集）并入iqiyi_copyright_details
    def save_copyright_movie(self):
        conn, cur = DataBase.open_conn_qidun()
        copyright_qipu_ids = set()
        copyright_doc_ids = set()
        copyright_doc_ids_used = set()
        copyright_doc_ids_movie = set()
        copyright_videos_movie = []
        copyright_videos = []

        cur.execute("SELECT qipu_id FROM copyright_videos where monitor = 1;")
        for data in cur.fetchall():
            # self.video_set.add(data[0])
            copyright_qipu_ids.add(data[0])
        cur.execute("SELECT doc_id,qipu_id,album_type,total_number,category_id,source_id,album_id,site_id FROM iqiyi_data WHERE qipu_id in (%s);" % (','.join(copyright_qipu_ids)) )
        for data in cur.fetchall():
            copyright_doc_ids.add(data[0])
        print len(copyright_qipu_ids)

        cur.execute("SELECT doc_id, tvid, video_title, link FROM iqiyi_copyright_details;")
        for data in cur.fetchall():
            if data[0] in copyright_doc_ids:
                copyright_videos.append(data)
                copyright_doc_ids_used.add(data[0])

        cur.execute("SELECT doc_id, tvid, video_title, link FROM iqiyi_details;")
        for data in cur.fetchall():
            doc_id = data[0]
            if doc_id in copyright_doc_ids and doc_id not in copyright_doc_ids_used:
                copyright_videos.append(data)
                copyright_doc_ids_movie.add('"'+doc_id+'"')
        copyright_doc_ids_movie_list = []
        for key in copyright_doc_ids_movie:
            copyright_doc_ids_movie_list.append(key)

        if len(copyright_doc_ids_movie_list)>0:
            sql_str = "SELECT doc_id,album_id,video_no,video_title,video_subtitle,video_site,link,image,online_time,qipu_id,tvid,vid,time_length,create_date,update_date FROM iqiyi_details WHERE doc_id in (%s);" % (','.join(copyright_doc_ids_movie_list))
            print sql_str
            cur.execute(sql_str)
            for data in cur.fetchall():
                copyright_videos_movie.append(data)

            cur.executemany('insert into iqiyi_copyright_details(doc_id,album_id,video_no,video_title,video_subtitle,'
                            'video_site,link,image,online_time,qipu_id,tvid,vid,time_length,create_date,update_date) '
                            'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', copyright_videos_movie)
            conn.commit()
        DataBase.close_conn(conn, cur)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    data = IqiyiData()
    data.crawler()
    data.clear_all()
    data.crawler_copyright()
    data.save_copyright_movie()