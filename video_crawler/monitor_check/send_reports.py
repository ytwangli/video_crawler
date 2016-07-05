#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import time
import datetime
import traceback
import threadpool
import MySQLdb
import smtplib
import email
from email.mime.text import MIMEText
from resource.http import HTMLResource,JsonResource

import bs4
from bs4 import BeautifulSoup

#
#
headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36', }

# mailto_list=['liyaning@qiyi.com']
# mailto_list=['liyaning@qiyi.com','lixi@qiyi.com']
mailto_list=['liyaning@qiyi.com','2718900138@qq.com','lixi@qiyi.com','303349130@qq.com']
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
        host='192.168.199.169',  # 192.168.199.169   10.1.230.90
        port=3306,
        user='root',
        passwd='iloveiqiyi',
        db='video_data',
        charset='utf8',
    )
    cur = conn.cursor()
    return conn, cur


def open_conn_r():
    conn = MySQLdb.connect(
        # host='192.168.199.169',
        host='sh.videomonitor.r.qiyi.db',
        port=8597,
        user='videomonitor',
        passwd='evPoLol4',
        db='videomonitor',
        charset='utf8',
    )
    cur = conn.cursor()
    # cur.execute("SET NAMES utf8mb4")
    return conn, cur

def open_conn_w():
    conn = MySQLdb.connect(
        # host='192.168.199.169',
        host='sh.videomonitor.w.qiyi.db',
        port=8597,
        user='videomonitor',
        passwd='evPoLol4',
        db='videomonitor',
        charset='utf8',
    )
    cur = conn.cursor()
    # cur.execute("SET NAMES utf8mb4")
    return conn, cur

def close_conn(conn, cur):
    cur.close()
    conn.close()

def get_tvid(table,host):
    data_list = []
    other_id_set = set()
    count = 0
    conn, cur = open_conn_r()
    # cur.execute('SELECT iqiyitvid, tudoudir, tudoutvid, sim_N, iqiyititle, tudoutitle FROM '+table + ' WHERE status =1 and sim_N >=3 ')
    # cur.execute('SELECT site,iqiyi_tvid, other_dir, other_tvid, other_url, sim_N, iqiyi_title, other_title FROM '+table + ' WHERE host=%s and status =1',(host,) )
    cur.execute('SELECT other_tvid FROM '+table + ' WHERE host=%s and status =1;',(host,) )
    for data in cur.fetchall():
        if data[0] not in other_id_set:
            count += 1
            other_id_set.add(data)
    close_conn(conn, cur)

    print 'other tv number='+ count
    return other_id_set

def get_monitor_info(table,host):
    data_list = []
    tvid_list = get_tvid(table,host)
    conn, cur = open_conn_r()
    for tvid in tvid_list:
        sum = 0
        cur.execute("SELECT site,iqiyi_tvid, other_dir, other_tvid, other_url, sim_N, iqiyi_title, other_title FROM "+table + " WHERE host=%s and status =1 and other_tvid =%s;",(host,tvid[0]) )
        for data in cur.fetchall():
            if data[5] >= 3:
                count = 0
                for monitor_info in data_list:
                    if tvid == monitor_info[3]:
                        count += 1
                if count == 0:
                    data_list.append(data)
                sum = 0
                break
            else:
                sum += data[5]
        # if sum >= 3:
        #     data_list.append(data)

    close_conn(conn, cur)
    return data_list,tvid_list

def get_monitor_info1(table,host):
    data_list = []
    tvid_list = get_tvid(table,host)
    conn, cur = open_conn_r()
    for tvid in tvid_list:
        sum = 0
        cur.execute("SELECT site,iqiyi_tvid, other_dir, other_tvid, other_url, sim_N, iqiyi_title, other_title FROM "+table + " WHERE host=%s and status =1 and other_tvid = %s;",(host,tvid[0]))
        for data in cur.fetchall():
            if data[5] >= 3:
                count = 0
                for monitor_info in data_list:
                    if tvid == monitor_info[3]:
                        count += 1
                if count == 0:
                    data_list.append(data)
                break
            else:
                sum += data[5]
        if sum >= 3:
            count = 0
            for monitor_info in data_list:
                if tvid == monitor_info[3]:
                    count += 1
            if count == 0:
                data_list.append(data)

    close_conn(conn, cur)
    return data_list,tvid_list


def get_result(table,host):
    data_list = []
    other_id_set = set()
    conn, cur = open_conn_r()
    # cur.execute('SELECT iqiyi_tvid, other_dir, other_tvid, sim_N, iqiyi_title, other_title FROM '+table + ' WHERE host=1 and status =1')
    cur.execute('SELECT site,iqiyi_tvid, other_dir, other_tvid, other_url, sim_N, iqiyi_title, other_title FROM '+table + ' WHERE host=%s and status =1;',(host,) )
    # cur.execute('SELECT iqiyitvid, tudoudir, tudoutvid, sim_N, iqiyititle, tudoutitle FROM '+table + ' WHERE status =1 and sim_N >=3 ')
    count = 0

    for data in cur.fetchall():
        if data[3] not in other_id_set:
            count += 1
            other_id_set.add(data[3])
            if data[5] >= 3:
                sum = 0
                for data1 in data_list:
                    if data[3] in data1:
                        sum += 1
                if sum == 0:
                    data_list.append(data)
                    # print "m--",data[3],data[5]
        else:
            if data[5] >= 3:
                sum = 0
                for data1 in data_list:
                    if data[3] in data1:
                        sum += 1
                if sum == 0:
                    data_list.append(data)
                    # print "n--",data[3],data[5]
    close_conn(conn, cur)
    print count
    return data_list,other_id_set


def get_info(table, id_str):
    conn, cur = open_conn_r()
    cur.execute('SELECT sid, duration, imageurl FROM '+table + ' WHERE id = '+id_str)
    for data in cur.fetchall():
        sid, duration, imageurl = data
    close_conn(conn, cur)
    return sid, duration, imageurl

def update_database(table,tvid_list,host):
    exe_time = datetime.datetime.now()
    conn_w, cur_w = open_conn_w()
    for tvid in tvid_list:
        # cur_w.execute('update '+table+' set status=2 where host=%s and other_tvid=' + tvid + ';',(host,))
        cur_w.execute("update "+table + " set status=2,update_date=%s where host=%s and other_tvid=%s;",(exe_time,host,tvid[0]))
    conn_w.commit()
    close_conn(conn_w, cur_w)

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

def filter(title):
    for bad_word in bad_words:
        if bad_word in title:
            return False

    return True

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

def check_bilibili(url):
    content = HTMLResource(url, headers=headers).get_resource()
    if content is not None:
        if u'<title>哔哩哔哩弹幕视频网 - ( ゜- ゜)つロ  乾杯~  - bilibili</title>' in content:
            return True
    else:
        return True
    return False

def send_reports(data_list,other_id_list):
    report_list = []
    for data in data_list:
        is_ok = 0
        is_offline = True
        if filter(data[7]):
            if data[0] == "tudou":
                is_offline = check_tudou(data[4])
            elif data[0] == "youku":
                is_offline = check_youku_off(data[4])
            elif data[0] == "letv":
                is_offline = check_letv(data[4])
            elif data[0] == "pptv":
                is_offline = check_pptv(data[4])
            elif data[0] == "sohu":
                is_offline = check_sohu(data[4])
            elif data[0] == "hunantv":
                is_offline = check_hunantv(data[4])
            elif data[0] == "funtv":
                is_offline = check_funtv(data[4])
            elif data[0] == "acfun":
                is_offline = check_acfun(data[4])
            elif data[0] == "bilibili":
                is_offline = check_bilibili(data[4])

            if is_offline == False:
                is_ok = 1
                item = '%s , %s , %s , %s , %s' % (data[4], data[6].strip(), data[7].strip(), is_ok,'\r\n')
                report_list.append(item)

            # content = HTMLResource(data[4], headers=headers).get_resource()
            # if content is not None:
            #     is_ok = 1
                # soup = BeautifulSoup(content)
            # item = '%s, %s, %s, %s %s' % (data[4], data[6].strip(), data[7].strip(), is_ok,'\n')
            # report_list.append(item)
            # try:
            #     data[6] = data[6].replace('\r','').replace('\n','')
            #     data[7] = data[7].replace('\r','').replace('\n','')
            # except Exception as e:
            #     data[6] = data[6].decode('gbk')
            #     data[7] = data[7].decode('gbk')
            #     data[6] = data[6].replace('\r','').replace('\n','')
            #     data[7] = data[7].replace('\r','').replace('\n','')
            # print '%s, %s, %s, %s' % (data[4], data[6], data[7], is_ok)

    if len(report_list):
        send_data = '\r\n'.join(report_list)
        if send_mail(mailto_list,"站外版权监控视频比对最新结果",send_data):
            update_database(report_table,other_id_list,PC_host)
            print "send mail ok !"
        else:
            print "Failed to send mail !"
    else:
        update_database(report_table,other_id_list,PC_host)
        print "no reports !"


#
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()
    print exe_time

    PC_host = 2
    report_table = 'report_data_new'

    # handle = open(filename1, 'r+')
    # data_list,other_id_list = get_result(report_table,PC_host)
    data_list,other_id_list = get_monitor_info(report_table,PC_host)
    send_reports(data_list,other_id_list)

    print "send reoports end !"