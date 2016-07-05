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

import numpy as np
import cv2
# from common import anorm, getsize
import struct
import os
import sys
sys.path.insert(0, '..')
import MySQLdb
import time
import datetime

FLANN_INDEX_KDTREE = 1  # bug: flann enums are missing
FLANN_INDEX_LSH    = 6

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
#         host='127.0.0.1',
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


def init_feature(name):
    chunks = name.split('-')
    if chunks[0] == 'sift':
        detector = cv2.SIFT()
        norm = cv2.NORM_L2
    elif chunks[0] == 'surf':
        detector = cv2.SURF(800)
        norm = cv2.NORM_L2
    elif chunks[0] == 'orb':
        detector = cv2.ORB(400)
        norm = cv2.NORM_HAMMING
    else:
        return None, None
    if 'flann' in chunks:
        if norm == cv2.NORM_L2:
            flann_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
            # print "flann"
        else:
            flann_params= dict(algorithm = FLANN_INDEX_LSH,
                               table_number = 6, # 12
                               key_size = 12,     # 20
                               multi_probe_level = 1) #2
        matcher = cv2.FlannBasedMatcher(flann_params, {})  # bug : need to pass empty dict (#1329)
    else:
        matcher = cv2.BFMatcher(norm)
    return detector, matcher


def filter_matches(kp1, kp2, matches, ratio = 0.75):
    mkp1, mkp2 = [], []
    for m in matches:
        if len(m) == 2 and m[0].distance < m[1].distance * ratio:
            m = m[0]
            mkp1.append( kp1[m.queryIdx] )
            mkp2.append( kp2[m.trainIdx] )
    p1 = np.float32([kp.pt for kp in mkp1])
    p2 = np.float32([kp.pt for kp in mkp2])
    kp_pairs = zip(mkp1, mkp2)
    return p1, p2, kp_pairs

def explore_match(win, img1, img2, kp_pairs, status = None, H = None):
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
    vis[:h1, :w1] = img1
    vis[:h2, w1:w1+w2] = img2
    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

    if H is not None:
        corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
        corners = np.int32( cv2.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
        cv2.polylines(vis, [corners], True, (255, 255, 255))

    if status is None:
        status = np.ones(len(kp_pairs), np.bool_)
    p1 = np.int32([kpp[0].pt for kpp in kp_pairs])
    p2 = np.int32([kpp[1].pt for kpp in kp_pairs]) + (w1, 0)

    green = (0, 255, 0)
    red = (0, 0, 255)
    white = (255, 255, 255)
    kp_color = (51, 103, 236)
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            col = green
            cv2.circle(vis, (x1, y1), 2, col, -1)
            cv2.circle(vis, (x2, y2), 2, col, -1)
        else:
            col = red
            r = 2
            thickness = 3
            cv2.line(vis, (x1-r, y1-r), (x1+r, y1+r), col, thickness)
            cv2.line(vis, (x1-r, y1+r), (x1+r, y1-r), col, thickness)
            cv2.line(vis, (x2-r, y2-r), (x2+r, y2+r), col, thickness)
            cv2.line(vis, (x2-r, y2+r), (x2+r, y2-r), col, thickness)
    vis0 = vis.copy()
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            cv2.line(vis, (x1, y1), (x2, y2), green)

    cv2.imshow(win, vis)
    def onmouse(event, x, y, flags, param):
        cur_vis = vis
        if flags & cv2.EVENT_FLAG_LBUTTON:
            cur_vis = vis0.copy()
            r = 8
            m = (anorm(p1 - (x, y)) < r) | (anorm(p2 - (x, y)) < r)
            idxs = np.where(m)[0]
            kp1s, kp2s = [], []
            for i in idxs:
                 (x1, y1), (x2, y2) = p1[i], p2[i]
                 col = (red, green)[status[i]]
                 cv2.line(cur_vis, (x1, y1), (x2, y2), col)
                 kp1, kp2 = kp_pairs[i]
                 kp1s.append(kp1)
                 kp2s.append(kp2)
            cur_vis = cv2.drawKeypoints(cur_vis, kp1s, flags=4, color=kp_color)
            cur_vis[:,w1:] = cv2.drawKeypoints(cur_vis[:,w1:], kp2s, flags=4, color=kp_color)

        cv2.imshow(win, cur_vis)
    cv2.setMouseCallback(win, onmouse)
    return vis


def surf_matches(fn1, fn2):
    feature_name = 'surf-flann'
    img1 = cv2.imread(fn1, 0)
    img2 = cv2.imread(fn2, 0)
    detector, matcher = init_feature(feature_name)
    # if detector != None:
    #     print 'using', feature_name
    # else:
    #     print 'unknown feature:', feature_name
    #     sys.exit(1)
    if img1 is not None and img2 is not None:
        kp1, desc1 = detector.detectAndCompute(img1, None)
        kp2, desc2 = detector.detectAndCompute(img2, None)
    else:
	return 0
    # print 'img1 - %d features, img2 - %d features' % (len(kp1), len(kp2))

    r_threshold = 0.75
    match_count = 0
    if len(kp1) > 1 and len(kp2) > 1 :
        raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2

        for m in raw_matches:
            if len(m) == 2 and m[0].distance < m[1].distance * r_threshold:
                match_count += 1

        min_match_count = 25
        if match_count >= min_match_count:
            # print 'match'
            return 1
        else:
            return 0
    else:
        return 0

def surf_matches1(fn1, fn2):
    feature_name = 'surf-flann'
    img1 = cv2.imread(fn1, 0)
    img2 = cv2.imread(fn2, 0)
    detector, matcher = init_feature(feature_name)
    if detector != None:
        print 'using', feature_name
    else:
        print 'unknown feature:', feature_name
        sys.exit(1)
    kp1, desc1 = detector.detectAndCompute(img1, None)
    kp2, desc2 = detector.detectAndCompute(img2, None)
    print 'img1 - %d features, img2 - %d features' % (len(kp1), len(kp2))

    r_threshold = 0.75
    match_count = 0
    if len(kp1) > 1 and len(kp2) > 1 :
        FLANN_INDEX_KDTREE = 1  # bug: flann enums are missing
        flann_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        flann = cv2.flann_Index(desc2, flann_params)
        idx2, raw_matches = flann.knnSearch(desc1, 2, params = {}) # bug: need to provide empty dict
        mask = raw_matches[:,0] / raw_matches[:,1] < r_threshold
        idx1 = np.arange(len(desc1))
        pairs = np.int32( zip(idx1, idx2[:,0]) )

        for m in raw_matches:
            if len(m) == 2 and m[0].distance < m[1].distance * r_threshold:
                match_count += 1

        min_match_count = 25
        print '%s' % (match_count)
        if match_count >= min_match_count:
            print 'match'
            return 1
        else:
            return 0
    else:
        return 0


def match_and_draw(win):
    fn1 = '/media/image/iqiyi/379551600/1_1481.jpg'
    fn2 = '/media/image/tudou/20150721/235693978/235693978_6.jpg'
    feature_name = 'surf-flann'
    img1 = cv2.imread(fn1, 0)
    img2 = cv2.imread(fn2, 0)
    detector, matcher = init_feature(feature_name)
    if detector != None:
        print 'using', feature_name
    else:
        print 'unknown feature:', feature_name
        sys.exit(1)
    kp1, desc1 = detector.detectAndCompute(img1, None)
    kp2, desc2 = detector.detectAndCompute(img2, None)
    print 'img1 - %d features, img2 - %d features' % (len(kp1), len(kp2))

    print 'matching...'
    if len(kp1) > 1 and len(kp2) > 1 :
        raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
        p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
        if len(p1) >= 4:
            H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
            print '%d / %d  inliers/matched' % (np.sum(status), len(status))
            # do not draw outliers (there will be a lot of them)
            kp_pairs = [kpp for kpp, flag in zip(kp_pairs, status) if flag]
        else:
            H, status = None, None
            print '%d matches found, not enough for homography estimation' % len(p1)

        vis = explore_match(win, img1, img2, kp_pairs, None, H)

    cv2.waitKey()
    cv2.destroyAllWindows()

def get_result_files(table,host):
    data_list = []
    conn_r, cur_r = open_conn_r()
    cur_r.execute('SELECT site,report_path FROM '+table+' WHERE host=%s AND status=1;',(host,))
    for data in cur_r.fetchall():
        data_list.append([data[0],data[1]])
    close_conn(conn_r, cur_r)
    return data_list

def update_database(table,file,host):
    conn_w, cur_w = open_conn_w()
    cur_w.execute('update '+table+' set status=2 where host=%s and report_path=\''+file+'\';',(host,))
    conn_w.commit()
    close_conn(conn_w, cur_w)


def parse_report_file(base_path,table,site_dict,host):
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()
    # table = 'compare_result'

    # path = base_path
    # for parent1,dirnames1,filenames1 in os.walk(path):
    # match_count = 0
    for site,filename1 in get_result_files(table,host):
        # if filename1.endswith('.csv'):
        if filename1[len(filename1)-4:len(filename1)] == '.csv':
            # handle = open(os.path.join(path,filename1), 'r+')
            handle = open(filename1, 'r+')
            if handle is None:
                continue
            info_list = []
            for line in handle.readlines():
                pos=line.find(',',0)
                image_path1 = line[0:pos]
                pos1=image_path1.rfind('/')
                tempstr = image_path1[0:pos1]
                pos1=tempstr.rfind('/')
                iqiyitvid = tempstr[pos1+1:len(tempstr)]
                # print iqiyitvid

                pos_t=line.find(',',pos+1)
                image_path2 = line[pos+1:pos_t]
                pos2=image_path2.rfind('/')
                tempstr2 = image_path2[0:pos2]
                pos3=tempstr2.rfind('/')
                othertvid = tempstr2[pos3+1:len(tempstr2)]
                tempstr2 = tempstr2[0:pos3]
                pos3=tempstr2.rfind('/')
                otherdir= tempstr2[pos3+1:len(tempstr2)]
                # match_count +=1
                if surf_matches(image_path1,image_path2) == 1:
                    #print "matchers ok"
                    if len(info_list)==0:
                        path_list = []
                        path_list.append(image_path2)
                        info_list.append(othertvid)
                        info_list.append(path_list)
                    else:
                        count=0
                        for num in range(0,len(info_list)/2) :
                            count1=0
                            if info_list[2*num] == othertvid:
                                for list in info_list[2*num+1]:
                                    if list != image_path2:
                                        count1 +=1

                                if count1 == len(info_list[2*num+1]):
                                    info_list[2*num+1].append(image_path2)

                            else:
                                count += 1

                        if count == (len(info_list)/2):
                            list =[]
                            list.append(image_path2)
                            info_list.append(othertvid)
                            info_list.append(list)

            handle.close()

            #print "start database"
            iqiyititle = "none"

            if site in site_dict.keys():
                obj_table = site + '_long'
                base_url = site_dict[site]
            else:
		        continue
	
            # conn2, cur2 = open_conn2()
            conn_r, cur_r = open_conn_r()
            if '_' in iqiyitvid:
                # print iqiyitvid +'->is ok'
                album_id = iqiyitvid.lstrip('_')
                # cur2.execute("select video_title from iqiyi_copyright_details where album_id=" +album_id + ";")
                cur_r.execute("select video_title from iqiyidata where album_id=" +album_id + ";")
                for data in cur_r.fetchall():
                    iqiyititle =  data[0]
            else:
                # cur2.execute("select video_title from iqiyi_copyright_details where tvid=" +iqiyitvid + ";")
                cur_r.execute("select video_title from iqiyidata where tvid=" +iqiyitvid + ";")
                for data in cur_r.fetchall():
                    iqiyititle =  data[0]

            #print iqiyititle

            # close_conn(conn2, cur2)
            # conn, cur = open_conn()
            # conn_r, cur_r = open_conn_r()
            conn_w, cur_w = open_conn_w()
            for num in range(0,len(info_list)/2) :
                tvid = info_list[2*num]
                pic_num = len(info_list[2*num+1])
                # cur.execute("select sid,title from tudou where id="+tvid+";")
                # cur_r.execute("select sid,title from tudou_long where id="+tvid+";")
                cur_r.execute("select id,sid,title from "+obj_table+" where id="+tvid+";")
                # for data1 in cur.fetchall():
                for data1 in cur_r.fetchall():
                    id =  data1[0]
                    sid =  data1[1]
                    othertitle =  data1[2]
		
                if site == "tudou":
                    url = base_url + sid + '/'
                elif site == "youku":
                    url = base_url + sid + '.html'
                elif site == "letv":
                    url = base_url + str(id) + '.html'
                elif site == "pptv":
                    url = base_url + sid + '.html'
                elif site == "sohu":
                    #sohu_sid = sid.split('/')
                    url = base_url + sid + '.shtml'
                elif site == "hunantv":
                    url = base_url + sid + '.html'
                elif site == "funtv":
                    url = base_url + str(id) + '/'
                elif site == "acfun":
                    url = base_url + str(sid)
                elif site == "bilibili":
                    url = base_url + str(sid)
                else:
		            continue

                print tvid
                print othertitle
                print url

                sql = 'insert into report_data_new(host,site,iqiyi_tvid,other_dir,other_tvid,other_url,sim_N, iqiyi_title,other_title,status,date_str,create_date,update_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                param = (host,site,iqiyitvid, otherdir,tvid, url,pic_num,iqiyititle,othertitle,1,date_str,exe_time,exe_time)
                # print sql % param
                cur_w.execute(sql, param)

            conn_w.commit()
            close_conn(conn_w, cur_w)
            close_conn(conn_r, cur_r)
            # close_conn(conn, cur)

            # update compare_result table
            update_database(table,filename1,host)

    # exe_time1 = datetime.datetime.now()
    # print 'start:%s ;end:%s;match count:%s'%(str(exe_time),str(exe_time1),str(match_count))

def parse_report_file1(base_path):
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()

    for parent,dirnames,filenames in os.walk(base_path):
        for dirname in  dirnames:
            path = base_path + dirname + '/'
            for parent1,dirnames1,filenames1 in os.walk(path):
                for filename1 in filenames1:
                    if filename1.endswith('.csv'):
                        handle = open(os.path.join(path,filename1), 'r+')
                        info_list = []
                        for line in handle.readlines():
                            pos=line.find(',',0)
                            image_path1 = line[0:pos]
                            pos1=image_path1.rfind('/')
                            tempstr = image_path1[0:pos1]
                            pos1=tempstr.rfind('/')
                            iqiyitvid = tempstr[pos1+1:len(tempstr)]
                            # print iqiyitvid

                            pos_t=line.find(',',pos+1)
                            image_path2 = line[pos+1:pos_t]
                            pos2=image_path2.rfind('/')
                            tempstr2 = image_path2[0:pos2]
                            pos3=tempstr2.rfind('/')
                            tudoutvid = tempstr2[pos3+1:len(tempstr2)]
                            tempstr2 = tempstr2[0:pos3]
                            pos3=tempstr2.rfind('/')
                            tudoudir= tempstr2[pos3+1:len(tempstr2)]

                            if surf_matches(image_path1,image_path2) == 1:
                                print "matchers ok"
                                if len(info_list)==0:
                                    path_list = []
                                    path_list.append(image_path2)
                                    info_list.append(tudoutvid)
                                    info_list.append(path_list)
                                else:
                                    count=0
                                    for num in range(0,len(info_list)/2) :
                                        count1=0
                                        if info_list[2*num] == tudoutvid:
                                            for list in info_list[2*num+1]:
                                                if list != image_path2:
                                                    count1 +=1

                                            if count1 == len(info_list[2*num+1]):
                                                info_list[2*num+1].append(image_path2)

                                        else:
                                            count += 1

                                    if count == (len(info_list)/2):
                                        list =[]
                                        list.append(image_path2)
                                        info_list.append(tudoutvid)
                                        info_list.append(list)

                                    print "end change tvid list"

                        handle.close()

                        print "start database"
                        conn2, cur2 = open_conn2()
                        cur2.execute("select video_title from iqiyi_copyright_details where tvid=" +iqiyitvid + ";")
                        for data in cur2.fetchall():
                            iqiyititle =  data[0]
                        close_conn(conn2, cur2)
                        print iqiyititle
                        conn_r, cur_r = open_conn_r()
                        conn_w, cur_w = open_conn_w()
                        for num in range(0,len(info_list)/2) :
                            tvid = info_list[2*num]
                            pic_num = len(info_list[2*num+1])
                            cur_r.execute("select title from tudou where id="+tvid+";")
                            for data1 in cur_r.fetchall():
                                tudoutitle =  data1[0]

                            print tvid
                            print tudoutitle

                            sql = 'insert into report_data_new(iqiyitvid,tudoudir,tudoutvid,sim_N, iqiyititle,tudoutitle,status,date_str,create_date,update_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
                            param = (iqiyitvid, tudoudir,tvid, pic_num,iqiyititle,tudoutitle,1,date_str,exe_time,exe_time)
                            # print sql % param
                            cur_w.execute(sql, param)

                        conn_w.commit()
                        close_conn(conn_w, cur_w)
                        close_conn(conn_r, cur_r)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    date_str = time.strftime("%Y%m%d", time.localtime())
    exe_time = datetime.datetime.now()
    print 'start time:',exe_time

    host = 2
    base_path = '/media/image/report/'
    table = 'compare_result'
    site_dict = {'tudou':'http://www.tudou.com/programs/view/',
                'youku':'http://v.youku.com/v_show/id_',
                'letv':'http://www.letv.com/ptv/vplay/',
                'sohu':'http://tv.sohu.com/',
                'pptv':'http://v.pptv.com/show/',
                'hunantv':'http://www.hunantv.com/',
                'funtv':'http://www.fun.tv/vplay/v-',
                'acfun':'http://www.acfun.tv/v/ac',
                'bilibili':'http://www.bilibili.com/video/av'}

    parse_report_file(base_path,table,site_dict,host)

    exe_time = datetime.datetime.now()
    print 'end time:',exe_time
    print "parse report file end !"


    # base_path = '/home/lixi/test/'
    # parse_report_file1(base_path)
    # match_and_draw('find_obj')

    '''
    import sys, getopt
    opts, args = getopt.getopt(sys.argv[1:], '', ['feature='])
    opts = dict(opts)
    feature_name = opts.get('--feature', 'sift')
    try: fn1, fn2 = args
    except:
        fn1 = '/media/image/iqiyi/379551600/1_1481.jpg'
        fn2 = '/media/image/tudou/20150721/235693978/235693978_6.jpg'

    feature_name = 'surf-flann'

    img1 = cv2.imread(fn1, 0)
    img2 = cv2.imread(fn2, 0)
    detector, matcher = init_feature(feature_name)
    if detector != None:
        print 'using', feature_name
    else:
        print 'unknown feature:', feature_name
        sys.exit(1)

    kp1, desc1 = detector.detectAndCompute(img1, None)
    kp2, desc2 = detector.detectAndCompute(img2, None)
    print 'img1 - %d features, img2 - %d features' % (len(kp1), len(kp2))

    def match_and_draw(win):
        print 'matching...'
        raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
        p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
        if len(p1) >= 4:
            H, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
            print '%d / %d  inliers/matched' % (np.sum(status), len(status))
        else:
            H, status = None, None
            print '%d matches found, not enough for homography estimation' % len(p1)

        vis = explore_match(win, img1, img2, kp_pairs, status, H)

    match_and_draw('find_obj')
    cv2.waitKey()
    cv2.destroyAllWindows()
    '''

