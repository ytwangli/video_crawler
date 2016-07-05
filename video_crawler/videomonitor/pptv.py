#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import random
import re
import time
import hashlib
from resource.http import HTMLResource, XmlResource

class PPTV():
    name = "PPTV (PPTV)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
                'Referer': 'http://player.aplus.pptv.com/corporate/proxy/proxy.html'
                }
    # http://web-play.pptv.com/webplay3-0-23531675.xml?zone=8&pid=12501&vvid=906a04d2-d8a9-3770-62c8-5de7de0a8050&version=4&username=&param=type%3Dweb.fpp%26userType%3D0%26o%3D-1&o=-1&referrer=&type=web.fpp&r=1453274422808
    # http://web-play.pptv.com/webplay3-0-23531675.xml?zone=8&pid=12501&vvid=906a04d2-d8a9-3770-62c8-5de7de0a8050&version=4&username=&param=type%3Dweb.fpp%26userType%3D0%26o%3D-1&pageUrl=http%3A%2F%2Fplayer.pplive.cn%2Fikan%2F3.4.1.0%2Fplayer4player2.swf%3Frcc%3D0%26pl%3Dpptv%253A%252F%252F0a2enKuYoaajnpzHraA%253D%26link%3Dhttp%253A%252F%252Fv.pptv.com%252Fshow%252Fm8kRjreaBEKlI4s.html%26swf%3Dhttp%253A%252F%252Fplayer.pptv.com%252Fv%252Fm8kRjreaBEKlI4s.swf%26pid%3D12501&o=-1&referrer=&type=web.fpp&r=1453274422808
    def video_info1(self, _id):
        try:
            # kk":"6fe0412f9546ae6e32604cd06487ed38-1b42-569efc38",
            # videoSrc:"http://web-play.pptv.com/web-m3u8-"+D+".m3u8?type="+A.loadType+"&playback=0"+B
            # url:"http://web-play.pptv.com/webplay3-0-"+D+".xml?version=4&type="+A.loadType+B,jsonp:"cb",
            url = 'http://web-play.pptv.com/webplay3-0-%s.xml?zone=8&pid=12501&vvid=906a04d2-d8a9-3770-62c8-5de7de0a8050&version=4&username=&param=%s&o=-1&referrer=&type=web.fpp&r=1453274422808' % (_id, 'type%3Dweb.fpp%26userType%3D0%26o%3D-1')
            content = XmlResource(url, headers=self.headers).get_resource()
            if 'error' in content['root']:
                ee = content['root']['error']
                if 'code' in ee:
                    return str(int(['code'])*-1-100)
                elif '@code' in ee:
                    return str(int(['@code'])*-1-100)
                else:
                    return '-100'
            # title = content['root']['channel']['@nm']
            rids = content['root']['channel']['file']['item']
            rid = None
            dt = None
            file_size = 0
            if '@vip' in rids:
                rid = rids
            else:
                for rid_tmp in rids:
                    if rid_tmp['@vip'] == '0':
                        file_size_tmp = int(rid_tmp['@filesize'])
                        if file_size_tmp > file_size:
                            rid = rid_tmp
                            file_size = file_size_tmp
            ft = rid['@ft']
            dts = content['root']['dt']
            if '@ft' in dts:
                dt = dts
            else:
                for dt_tmp in dts:
                    if dt_tmp['@ft'] == ft:
                        dt = dt_tmp
                        break
            host = dt['sh']
            k = dt['key']['#text']
            # http://221.194.64.51/3/4f544021fcbf563ece26742292804530.mp4?fpp.ver=1.3.0.19&key=533bb00deb4b933599661cce406b0bb5&k=7e3cb36df094d5a25a176492907ca216-39d1-1453288805&type=web.fpp
            url = "http://{}/0/{}.mp4?fpp.ver=1.3.0.19&key={}&k={}&type=web.fpp".format(host,rid['@rid'].replace('.mp4', ''),k,dt['id'])
            print url
            # url = "http://{}/w/{}.m3u8?platform=android3&type=phone.android&k={}".format(host,rid['@rid'].replace('.mp4', ''),k)
            return url
        except Exception as e:
            traceback.print_stack()
            print e
            print _id
        return '-1'

http://221.194.64.61/0/f550ff7375ff3900a999a9c048ebc775.mp4?fpp.ver=1.3.0.19&key=44cd1e328aa7dbc43c2d73d3df057645-9e3c-1453882689&k=de2ece6a7e04b6c7d6a8956634c8c12d&type=web.fpp
# 'http://jump.synacast.com/ef6864dc6406e393b9374a5a186df7d0.mp4dt?type=web&t=0.313389744'
# 'http://8.8.8.8/0/ef6864dc6406e393b9374a5a186df7d0.mp4?key=5b07ece834e7eb4ab5da179f6d65e0b6'

# 'http://jump.synacast.com/ef6864dc6406e393b9374a5a186df7d0.mp4dt?type=web&t=0.313389744'
# 'http://8.8.8.8/0/ef6864dc6406e393b9374a5a186df7d0.mp4?key=5b07ece834e7eb4ab5da179f6d65e0b6'
    def video_info(self, _id):
        try:
            # kk":"6fe0412f9546ae6e32604cd06487ed38-1b42-569efc38",
            # videoSrc:"http://web-play.pptv.com/web-m3u8-"+D+".m3u8?type="+A.loadType+"&playback=0"+B
            # url:"http://web-play.pptv.com/webplay3-0-"+D+".xml?version=4&type="+A.loadType+B,jsonp:"cb",
            url = 'http://web-play.pptv.com/webplay3-10-%s.xml?platform=android4&type=phone.android&version=4' % (_id)
            content = XmlResource(url, headers=self.headers).get_resource()
            if 'error' in content['root']:
                ee = content['root']['error']
                if 'code' in ee:
                    return str(int(['code'])*-1-100)
                elif '@code' in ee:
                    return str(int(['@code'])*-1-100)
                else:
                    return '-100'
            # title = content['root']['channel']['@nm']
            rids = content['root']['channel']['file']['item']
            rid = None
            dt = None
            file_size = 0
            if '@vip' in rids:
                rid = rids
            else:
                for rid_tmp in rids:
                    if rid_tmp['@vip'] == '0':
                        file_size_tmp = int(rid_tmp['@filesize'])
                        if file_size_tmp > file_size:
                            rid = rid_tmp
                            file_size = file_size_tmp
            ft = rid['@ft']
            dts = content['root']['dt']
            if '@ft' in dts:
                dt = dts
            else:
                for dt_tmp in dts:
                    if dt_tmp['@ft'] == ft:
                        dt = dt_tmp
                        break
            host = dt['sh']
            k = dt['key']['#text']
            url = "http://{}/w/{}.mp4?platform=android3&type=phone.android&k={}".format(host,rid['@rid'].replace('.mp4', ''),k)
            print url
            # url = "http://{}/w/{}.m3u8?platform=android3&type=phone.android&k={}".format(host,rid['@rid'].replace('.mp4', ''),k)
            return url
        except Exception as e:
            traceback.print_stack()
            print e
            print _id
        return '-1'



    # def get_vvid(self, _id):
    #     # m2 = hashlib.md5()
    #     # m2.update(str(int(time.time())))
    #     # hash_str = m2.hexdigest()
    #     # vvid = "%s-%s-%s-%s-%s" % (hash_str[1: 8], hash_str[9: 12], hash_str[13: 16], hash_str[17: 20], hash_str[21: ])
    #
    #
    #     # "http://play.api.pptv.com/boxplay.api?id=%s&platform=atv&canal=9122&ver=3&lang=zh_CN&vvid=%s&type=tv.android&gslbversion=2&userLevel=0&open=0&content=need_drag"
    #     fmt_url = "http://play.api.pptv.com/boxplay.api?auth=d410fafad87e7bbf6c6dd62434345818&userLevel=0&id=%s&sv=4.1.3&ver=1&type=phone.android&k_ver=1.1.0.8537&gslbversion=2&content=need_drag&platform=android3"
    #     content = XmlResource(fmt_url % _id, headers=self.pcheaders).get_resource()
    #     print content

    def parse(self, _id):
        try:
            url = self.video_info1(_id)
            return url
        except Exception as e:
            traceback.print_stack()
            print e
            print _id
        return '-1'

    def get_headers(self):
        return self.headers

# http://v.pptv.com/show/m8kRjvZczApt61M.html
# http://v.pptv.com/show/u1KgH4ftXZvibfOQ.html
# http://web-play.pptv.com/webplay3-10-24096699.xml?platform=android4&type=phone.android&version=4
# http://221.194.64.55/w/1066be0d54ecfa6794726073f7403b23.mp4?platform=android3&type=phone.android&k=02863045df9ebe281effe8f924bef57c-e75e-1452608802
# http://221.194.64.55/w/1066be0d54ecfa6794726073f7403b23.m3u8?platform=android3&type=phone.android&k=02863045df9ebe281effe8f924bef57c-e75e-1452608802
# http://player.pptv.com/v/m8kRjreaBEKlI4s.swf
# http://player.pplive.cn/ikan/3.4.1.0/player4player2.swf?rcc=0&pl=pptv%3A%2F%2F0a2enKuYoaajnpzHraA%3D&link=http%3A%2F%2Fv.pptv.com%2Fshow%2Fm8kRjreaBEKlI4s.html&swf=http%3A%2F%2Fplayer.pptv.com%2Fv%2Fm8kRjreaBEKlI4s.swf&pid=12501
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    url = PPTV().parse('23531675')
    print url
    url = PPTV().parse('24034725')
    print url

    # HTMLResource('', headers=headers).download_video_ts(urls, 'D:\\24032705.ts', 1024*1024*60)