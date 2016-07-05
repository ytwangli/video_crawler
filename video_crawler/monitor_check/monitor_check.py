#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

'''
Feature-based image matching sample.

USAGE
  find_obj.py [--feature=<sift|surf|orb>[-flann]] [ <image1> <image2> ]

  --feature  - Feature to use. Can be sift, surf of orb. Append '-flann' to feature name
                to use Flann-based matcher instead bruteforce.

  Press left mouse button on a feature point to see its matching point.
'''

# import numpy as np
# import cv2
# from common import anorm, getsize
import struct
import os
import sys
sys.path.insert(0, '..')
import time
import datetime
import MySQLdb
# from resource.database import DataBase
import threadpool
import traceback
import smtplib
import email
from email.mime.text import MIMEText
from resource.http import HTMLResource,JsonResource


try:
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:
    from urllib.request import urlopen, Request, HTTPError, URLError
from bs4 import BeautifulSoup
# import urllib
# from check_offline import *



headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36', }

# mailto_list=['liyaning@qiyi.com']
mailto_list=['liyaning@qiyi.com','lixi@qiyi.com']
# mailto_list=['liyaning@qiyi.com','2718900138@qq.com','lixi@qiyi.com','303349130@qq.com']
mail_host="smtp.126.com"  #设置服务器
mail_username="zurzer"    #用户名
mail_password="temexaofwgoykpnm"   #口令
#mail_postfix="XXX.com"  #发件箱的后缀

bad_words = [
    u'云帆搜索', u'剧情介绍', u'剧情简介', u'人物介绍', u'资料搜索', u'演员表', u'故事梗概', u'分集剧情', u'预告',
    u'小说', u'txt', u'TXT', u'MV', u'观后感', u'主题曲', u'剧照', u'影评', u'花絮', u'上映时间', u'电影票', u'海报',
    u'壁纸', u'mp3', u'MP3',u'wav', u'WAV', u'LOGO', u'发布会', u'彩蛋', u'见面会', u'特辑', u'首映礼', u'宣传片', u'片尾曲', u'图片素材',
    u'教学视频', u'视频教程', u'新闻', u'广播',u'实况',u'游戏', u'剧评'
]


def open_conn():
    conn = MySQLdb.connect(
        host='10.1.230.44',
        # host='127.0.0.1',
        port=3306,
        user='root',
        passwd='iloveiqiyi',
        db='video_data',
        charset='utf8',
    )
    cur = conn.cursor()
    cur.execute("SET NAMES utf8")
    return conn, cur

def open_conn_r():
    conn = MySQLdb.connect(
        host='sh.videomonitor.r.qiyi.db',
        # host='127.0.0.1',
        port=8597,
        user='videomonitor',
        passwd='evPoLol4',
        db='videomonitor',
        charset='utf8',
    )
    cur = conn.cursor()
    cur.execute("SET NAMES utf8")
    return conn, cur

def open_conn_w():
    conn = MySQLdb.connect(
        host='sh.videomonitor.w.qiyi.db',
        # host='127.0.0.1',
        port=8597,
        user='videomonitor',
        passwd='evPoLol4',
        db='videomonitor',
        charset='utf8',
    )
    cur = conn.cursor()
    cur.execute("SET NAMES utf8")
    return conn, cur

def open_conn2():
    conn = MySQLdb.connect(
        host='lixi-videomonitor-copyright-dev001-shjj.qiyi.virtual',
        # host='127.0.0.1',
        port=3306,
        user='root',
        passwd='iloveiqiyi',
        db='dashboard',
        charset='utf8',
    )
    cur = conn.cursor()
    return conn, cur


def close_conn(conn, cur):
    cur.close()
    conn.close()




def update_database(table,file,host):
    conn_w, cur_w = open_conn_w()
    cur_w.execute('update '+table+' set status=2 where host=%s and report_path=\''+file+'\';',(host,))
    conn_w.commit()
    close_conn(conn_w, cur_w)

def get_keyword():
    keyword_list = []
    other_id_set = set()
    # conn, cur = DataBase.open_conn_video()
    conn, cur = open_conn_r()
    cur.execute("select video_title, album_id from iqiyidata where used_flag>0 and host=2;")
    for data in cur.fetchall():
        if data[1] not in other_id_set:
            other_id_set.add(data[1])
            keyword_list.append(data[0])

    # DataBase.close_conn(conn, cur)
    close_conn(conn, cur)
    return keyword_list

def parse_keyword():
    data_list = get_keyword()
    keyword_info = [u'小南的迷你情人']
    for data in data_list:
        data1 = data.split('_')
        data2 = data1[0].split()
        data3 = data2[0].split(u"第")
        data4 = data3[0].split(u"之")
        if data4[0] == u"流行":
            data4[0] = u"流行之王"
        elif data4[0] == u"Show":
            data4[0] = u"Show By Rock"
        elif data4[0] == u"奔跑吧兄弟":
            data4[0] = u"奔跑吧兄弟第3季"
        elif data4[0] == u"二龙湖浩哥":
            data4[0] = u"二龙湖浩哥之狂暴之路"
        # print data4[0]
        if data4[0] not in keyword_info:
            keyword_info.append(data4[0])
    return keyword_info

def get_oplog(site):
    data_list = []
    # conn, cur = DataBase.open_conn_video()
    conn, cur = open_conn_r()
    # test
    # cur.execute("select id, site, id_start, id_end, num, num_long from oplog where id=8 or id=13 or id=15 or id=16 or id=19 or id=102 or id =678;")
    # cur.execute("select id, site, id_start, id_end, num, num_long from oplog where status=1 and site=%s;",(site,))
    cur.execute("select id, site, id_start, id_end, num, num_long from oplog where status=0 and site=%s order by id asc LIMIT 32;",(site,))
    for data in cur.fetchall():
        data_list.append(data)

    # DataBase.close_conn(conn, cur)
    close_conn(conn, cur)
    return data_list

def get_datas(_data,keyword_list):
    data_list = []
    id, site, id_start, id_end, num, num_long = _data
    # id_start = 244118364
    # id_end = 244122160
    if id_start > id_end:
        _id_start = id_end
        _id_end = id_start
    else:
        _id_start = id_start
        _id_end = id_end
    conn, cur = open_conn_r()
    if num > 0:
        for keyword in keyword_list:
            if site == 'acfun':
                # cur.execute("SELECT id, sid, title FROM "+site+" WHERE sid<="+str(_id_start)+" and duration>500 and title like '%%%s%%';" %keyword)
                cur.execute("SELECT id, sid, title FROM "+site+" WHERE sid>="+str(_id_start)+" and sid<="+str(_id_end)+" and duration>500 and title like '%%%s%%';" %keyword)
            else:
                # cur.execute("SELECT id, sid, title FROM "+site+" WHERE id<="+str(_id_start)+" and duration>500 and title like '%%%s%%';" %keyword)
                cur.execute("SELECT id, sid, title FROM "+site+" WHERE id>="+str(_id_start)+" and id<="+str(_id_end)+" and duration>500 and title like '%%%s%%';" %keyword)
                # cur.execute("SELECT id, sid, title FROM "+site+" WHERE id>=%s and id<=%s and duration>0 and title like '%%%s%%';",(str(_id_start),str(_id_end),keyword))
            for data_short in cur.fetchall():
                data_list.append(data_short)
    if num_long > 0:
        for keyword in keyword_list:
            if site == 'acfun':
                # cur.execute("SELECT id, sid, title FROM "+site+"_long WHERE sid<="+str(_id_start)+" and duration>500 and title like '%%%s%%';" %keyword)
                cur.execute("SELECT id, sid, title FROM "+site+"_long WHERE sid>="+str(_id_start)+" and sid<="+str(_id_end)+" and duration>500 and title like '%%%s%%';" %keyword)
            else:
                # cur.execute("SELECT id, sid, title FROM "+site+"_long WHERE id<="+str(_id_start)+" and duration>500 and title like '%%%s%%';" %keyword)
                cur.execute("SELECT id, sid, title FROM "+site+"_long WHERE id>="+str(_id_start)+" and id<="+str(_id_end)+" and duration>500 and title like '%%%s%%';" %keyword)
                # cur.execute("SELECT id, sid, title FROM "+site+"_long WHERE id>=%s and id<=%s and duration>0 and title like '%%%s%%';",(str(_id_start),str(_id_end),keyword))
            for data_long in cur.fetchall():
                data_list.append(data_long)

    # DataBase.close_conn(conn, cur)
    close_conn(conn, cur)
    return data_list

def update_oplog(id):
    conn, cur = open_conn_w()
    cur.execute('update oplog set status=1 where id=%s;',(id,))
    conn.commit()
    close_conn(conn, cur)

def update_oplog_list(list):
    conn, cur = open_conn_w()
    for id in list:
        cur.execute('update oplog set status=1 where id=%s;',(id[0],))
    conn.commit()
    close_conn(conn, cur)

def check_database(site_dict,keyword_list):
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()

    data_list = []
    oplog_id_list = []
    check_list = []
    is_offline = True
    # test
    # data_list = get_oplog('youku')
    for site in site_dict.keys():
        base_url = site_dict[site]
        data_list = get_oplog(site)
        for data in data_list:
            if site==data[1]:
                oplog_id_list.append([data[0],data[1]])
                info_list = get_datas(data,keyword_list)
                for info in info_list:
                    id = info[0]
                    sid = info[1]
                    othertitle = info[2]
                    is_offline = True
                    if filter(othertitle):
                        if site == "tudou":
                            url = base_url + sid + '/'
                            is_offline = check_tudou(url)
                        elif site == "youku":
                            url = base_url + sid + '.html'
                            # is_offline = check_youku(url)
                            is_offline = check_youku_off(url)
                            # is_offline = check_link(url)
                        elif site == "letv":
                            if u'爱上超模' not in othertitle:
                                url = base_url + str(id) + '.html'
                                is_offline = check_letv(url)
                        elif site == "pptv":
                            url = base_url + sid + '.html'
                            is_offline = check_pptv(url)
                        elif site == "sohu":
                            url = base_url + sid + '.shtml'
                            is_offline = check_sohu(url)
                        elif site == "hunantv":
                            url = base_url + sid + '.html'
                            is_offline = check_hunantv(url)
                        elif site == "funtv":
                            url = base_url + str(id) + '/'
                            is_offline = check_funtv(url)
                        elif site == "acfun":
                            url = base_url + str(sid)
                            is_offline = check_acfun(url)
                        elif site == "bilibili":
                            url = base_url + str(sid)
                            is_offline = check_bilibili(url)
                        elif site == "baofeng":
                            url = base_url + str(id%1000)+'/play-'+str(id)+'.html'
                            is_offline = check_baofeng(url)
                        elif site == "wasu":
                            url = base_url + str(id)
                            is_offline = check_wasu(url)

                        if is_offline == False:
                            check_list.append([url,othertitle])
                        # print sid, url,othertitle

    return oplog_id_list,check_list


def send_mail(to_list,sub,content):
    send_from ="zurzer@126.com"
    msg = MIMEText(content,_subtype='plain',_charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = send_from
    msg['To'] = ";".join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_username,mail_password)
        server.sendmail(send_from, to_list, msg.as_string())
        server.close()
        return True
    except Exception, e:
        print str(e)
        return False

def send_check_data(send_data):
    report_list = []
    send_report = ''
    count = 0
    for data in send_data:
        # is_ok = 0
        # if check_link(data[0]):
        is_ok = 1
        item = str(data[0])+' ,'+str(data[1].strip())+' ,'+str(is_ok)+' ,\r\n'
        report_list.append(item)
        # try:
        #     data[1] = data[1].replace('\r', '').replace('\n', '')
        # except Exception as e:
        #     data[1] = data[1].decode('gbk')
        #     data[1] = data[1].replace('\r', '').replace('\n', '')
        # print '%s, %s, %s' % (data[0], data[1].replace('\n', ''), is_ok)
        # count += 1
        # status = urllib.urlopen(data[0]).code
        # print status
    # print 'sum:',count

    if len(report_list) > 0:
        send_report = '\r\n'.join(report_list)
        if send_mail(mailto_list,u"站外版权监控文字比对最新结果",send_report):
            print "send mail ok !"
        else:
            print "Failed to send mail !"
    else:
        print "no reports !"

def filter(title):
    for bad_word in bad_words:
        if bad_word in title:
            return False
    if u'讲鬼故事' in title:
        return False
    elif u'听书迷' in title or 'www.tingshumi.com' in title:
        return False
    elif u'解说' in title :
        return False
    elif u'我的世界' in title:
        return False
    elif u'票房排行榜' in title:
        return False
    elif u'揭秘' in title:
        return False
    elif u'片花' in title:
        return False

    return True

def build_request(url, data=None, headers={}):
    # headers['User-Agent'] = 'Dynamsoft'
    headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36'
    return Request(url, data=data, headers=headers)

def check_link(url):
     # teest
     # link = u'http://v.youku.com/v_show/id_XMTI2MTY4MDk2MA==.html'
    link = url
    try:
        # content = HTMLResource(data[0], headers=headers).get_resource()
        # if content is not None:
        request = build_request(link)
        f = urlopen(request)
        link_get = f.url
        status_code = f.code
        f.close()
    except HTTPError, URLError:
        status_code = URLError.code
    if status_code == 404:
        # print status_code
        return False
    else:
        if link == link_get:
            return True
        else:
            return False


def check_tudou(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location is None:
        print url
    if location == '404' or location.startswith('http://www.tudou.com/error.php'):
        return True
    content = HTMLResource(url, headers=headers).get_resource()
    if ",tvcCode: '-1'" not in content:
        return True
    return False

def check_youku_off(url):
    try:
        location = str(HTMLResource(url, headers=headers).get_Location())
        if location is not None:
            if location.startswith('http://www.youku.com/index/y404/') or location == '404':
                return True
        else:
            return True
    except Exception as e:
        return False
    return False

def check_sohu(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location == '404':
        return True
    else:
        content = HTMLResource(url, headers=headers).get_resource()
        if "<title>404页 - 搜狐视频</title>" in content:
            return True
    return False


def check_hunantv(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location.startswith('http://www.hunantv.com/') or location == '404':
        return True
    return False

def check_funtv(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location is not None:
        if location == '404':
            return True
        else:
            content = HTMLResource(url, headers=headers).get_resource()
            if content is not None:
                if "<h2>很抱歉，您访问的页面丢失啦~</h2>" in content:
                    return True
            else:
                return True
    else:
        return True
    return False

def check_acfun(url):
    # if not url.endswith('.aspx '):
    #     url = HTMLResource(url, headers=headers).get_Location()
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location == '403':
        return True
    else:
        content = HTMLResource(url, headers=headers).get_resource()
        if content is not None:
            if "<title>您查看的页面并不存在</title>\r\n    </head>" in content:
                return True
        else:
            return True
    return False

def check_bilibili(url):
    content = HTMLResource(url, headers=headers).get_resource()
    if content is not None:
        if u'<title>哔哩哔哩弹幕视频网 - ( ゜- ゜)つロ  乾杯~  - bilibili</title>' in content:
            return True
    else:
        return True
    return False

def check_pptv(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    location2 = str(HTMLResource(location, headers=headers).get_Location())
    if location2 == 'http://www.pptv.com/404' or location2 == '403':
        return True
    else:
        content = HTMLResource(location2, headers=headers).get_resource()
        if "<title>404 - 非常抱歉，您访问的页面不存在        -PPTV聚力-始终和你同一频道</title>" in content:
            return True
    return False

def check_letv(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location == '404':
        return True
    else:
        content = HTMLResource(url, headers=headers).get_resource()
        if "<title>出错提示_乐视网</title>" in content:
            return True
    return False

def check_baofeng(url):
    u'http://www.baofeng.com/detail/268/detail-791268.html'
    if 'detail-' in url:
        index = url.find('detail-')+7
        vid = url[index: url.find('.', index)]
    else:
        index = url.find('play-')+5
        vid = url[index: url.find('.', index)]
    check_url_hd = 'http://b3.ploy.baofeng.net/m/'+vid+'?from=hdbf&g=1&uid=63e34499f66474a19e74cda9bffb1f638a6ab120'
    content_hd = JsonResource(check_url_hd, headers=headers).get_resource()
    check_url_sd = 'http://b3.ploy.baofeng.net/m/'+vid+'?from=sdbf'
    content_sd = JsonResource(check_url_sd, headers=headers).get_resource()
    if int(content_hd['s']) == 0 and int(content_sd['s']) == 0:
        return True
    return False

def check_wasu(url):
    location = str(HTMLResource(url, headers=headers).get_Location())
    if location is not None:
        if location.startswith('http://www.wasu.cn') or location == '404':
            return True
    else:
        return True

    return False

#
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()
    print exe_time

    oplog_id = []
    send_data = []
    site_dict = {'tudou':'http://www.tudou.com/programs/view/',
                'youku':'http://v.youku.com/v_show/id_',
                'letv':'http://www.letv.com/ptv/vplay/',
                'sohu':'http://tv.sohu.com/',
                'pptv':'http://v.pptv.com/show/',
                'hunantv':'http://www.hunantv.com/',
                'funtv':'http://www.fun.tv/vplay/v-',
                'acfun':'http://www.acfun.tv/v/ac',
                'bilibili':'http://www.bilibili.com/video/av',
                'baofeng':'http://www.baofeng.com/play/',
                'wasu':'http://www.wasu.cn/wap/Play/show/id/'}

    # test
    # url = http://www.baofeng.com/play/82/play-784582.html
    # url = 'http://www.letv.com/ptv/vplay/22890255.html'
    # url = 'http://www.bilibili.com/video/av2471347'
    # print check_bilibili(url)
    # keyword_list = [u'奔跑吧兄弟第3季']
    keyword_list = parse_keyword()
    print 'check keyword :'
    for data in keyword_list:
        print data
    print 'start check ...'
    oplog_id,send_data = check_database(site_dict,keyword_list)
    for id in oplog_id:
        print "check finish oplog id : %s ->%s" %(id[0],id[1])
    #send check data by email
    send_check_data(send_data)
    update_oplog_list(oplog_id)
    print "check database end !"



