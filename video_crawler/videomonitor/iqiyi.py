#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

__all__ = ['iqiyi_download']

import sys
from resource.http import HTMLResource, JsonResource
from uuid import uuid4
from random import random,randint
import re
from math import floor
import hashlib
import traceback

'''
Changelog:
-> http://www.iqiyi.com/common/flashplayer/20150710/MainPlayer_5_2_25_c3_3_5_1.swf

-> http://www.iqiyi.com/common/flashplayer/20150703/MainPlayer_5_2_24_1_c3_3_3.swf
    SingletonClass.ekam

-> http://www.iqiyi.com/common/flashplayer/20150618/MainPlayer_5_2_24_1_c3_3_2.swf
    In this version Z7elzzup.cexe,just use node.js to run this code(with some modification) and get innerkey.

-> http://www.iqiyi.com/common/flashplayer/20150612/MainPlayer_5_2_23_1_c3_2_6_5.swf
    In this version do not directly use enc key
    gen enc key (so called sc ) in DMEmagelzzup.mix(tvid) -> (tm->getTimer(),src='hsalf',sc)
    encrypy alogrithm is md5(DMEmagelzzup.mix.genInnerKey +tm+tvid)
    how to gen genInnerKey ,can see first 3 lin in mix function in this file
'''

class Iqiyi(object):
    name = u"爱奇艺 (Iqiyi)"

    headers = {
                'User-Agent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.20 Safari/537.36',
                'Referer': 'http://www.iqiyi.com',
                'Cookie': 'P00001=afNHV8CBb6BHl2OG2yhJ5MWWSJm1m2BHoLac9zQi8xq0YNom49f',  # dolby_account_50@qiyi.com
                }

    bid_dict = {
        0: 'none',
        1: 'standard',  # 688 x 360
        2: 'high',  # 960 x 504   848 x 360
        3: 'super',
        4: 'suprt-high', # 1280 x 672  1280 x 544
        5: 'fullhd',  # 1920 x 1000  1920 x 816
        10: '4k',
        96: 'topspeed',  # 416 x 216
    }

    def mix(self, tvid):
        enc = []
        enc.append('6ab6d0280511493ba85594779759d4ed')
        tm = str(randint(2000,4000))
        src = 'eknas'
        enc.append(str(tm))
        enc.append(tvid)
        # sc = hashlib.new('md5',bytes("".join(enc),'utf-8')).hexdigest()
        sc = hashlib.new('md5',"".join(enc)).hexdigest()
        return tm,sc,src

    def getVRSXORCode(self, arg1,arg2):
        loc3=arg2 %3
        if loc3 == 1:
            return arg1^121
        if loc3 == 2:
            return arg1^72
        return arg1^103


    def getVrsEncodeCode(self, vlink):
        loc6=0
        loc2=''
        loc3=vlink.split("-")
        loc4=len(loc3)
        # loc5=loc4-1
        for i in range(loc4-1,-1,-1):
            loc6=self.getVRSXORCode(int(loc3[loc4-i-1],16),i)
            loc2+=chr(loc6)
        return loc2[::-1]

    def getVMS(self, tvid,vid,uid):
        #tm ->the flash run time for md5 usage
        #um -> vip 1 normal 0
        #authkey -> for password protected video ,replace '' with your password
        #puid user.passportid may empty?
        #TODO: support password protected video
        tm,sc,src = self.mix(tvid)
        vmsreq='http://cache.video.qiyi.com/vms?key=fvip&src=1702633101b340d8917a69cf8a4b8c7' +\
                    "&tvId="+tvid+"&vid="+vid+"&vinfo=1&tm="+tm+\
                    "&enc="+sc+\
                    "&qyid="+uid+"&tn="+str(random()) +"&um=0" +\
                    "&authkey="+hashlib.new('md5',''+str(tm)+tvid).hexdigest()
        # vmsreq='http://cache.vip.qiyi.com/vms?key=fvip&src=1702633101b340d8917a69cf8a4b8c7' +\
        #             "&tvId="+tvid+"&vid="+vid+"&vinfo=1&tm="+tm+\
        #             "&enc="+sc+\
        #             "&qyid="+uid+"&tn="+str(random()) +"&um=0" +\
        #             "&authkey="+hashlib.new('md5',''+str(tm)+tvid).hexdigest()+'&puid=&um=0&thdk=&thdt='
        content = JsonResource(vmsreq, headers=self.headers).get_resource()
        return content
    # &cid=afbe8fd3d73448c9&token=6f8b51a75784c34c2163a3989516be88&uid=1073813191&pf=b6c13e26323c537d

    def getDispathKey(self, rid):
        tp=")(*&^flash@#$%a"  #magic from swf
        url = "http://data.video.qiyi.com/t?tn="+str(random())
        time=JsonResource(url, headers=self.headers).get_resource()["t"]
        t=str(int(floor(int(time)/(10*60.0))))
        return hashlib.new("md5",t+tp+rid).hexdigest()

    # DEPRECATED in favor of match1()
    def r1(self, pattern, text):
        m = re.search(pattern, text)
        if m:
            return m.group(1)

    # DEPRECATED in favor of match1()
    def r1_of(self, patterns, text):
        for p in patterns:
            x = self.r1(p, text)
            if x:
                return x

    def parse_url(self, url):
        html = HTMLResource(url, headers=self.headers).get_resource()

        tvid = self.r1(r'data-player-tvid="([^"]+)"', html) or self.r1(r'tvid=([^&]+)', url)
        videoid = self.r1(r'data-player-videoid="([^"]+)"', html) or self.r1(r'vid=([^&]+)', url)
        self.parse(tvid, videoid)

    def parse(self, tvid, videoid):
        try:
            data = {}
            gen_uid=uuid4().hex

            info = self.getVMS(tvid, videoid, gen_uid)

            assert info["code"] == "A000000"

            title = info["data"]["vi"]["vn"]

            # data.vp = json.data.vp
            #  data.vi = json.data.vi
            #  data.f4v = json.data.f4v
            # if movieIsMember data.vp = json.data.np

            #for highest qualities
            #for http://www.iqiyi.com/v_19rrmmz5yw.html  not vp -> np
            try:
                if info["data"]['vp']["tkl"]=='' :
                    raise ValueError
            except:
                print("[Error] Do not support for iQIYI VIP video. "+str(tvid))
                return None

            bid = 5
            for i in info["data"]["vp"]["tkl"][0]["vs"]:
                bid=int(i["bid"])
                bid_name = self.bid_dict[bid]
                # if int(i["bid"])<=10 and int(i["bid"])>=bid:
                video_links=i["fs"] #now in i["flvs"] not in i["fs"]
                if not i["fs"][0]["l"].startswith("/"):
                    tmp = self.getVrsEncodeCode(i["fs"][0]["l"])
                    if tmp.endswith('mp4'):
                         video_links = i["flvs"]


                urls=[]
                size=0
                for i in video_links:
                    vlink=i["l"]
                    if not vlink.startswith("/"):
                        #vlink is encode
                        vlink=self.getVrsEncodeCode(vlink)
                    key=self.getDispathKey(vlink.split("/")[-1].split(".")[0])
                    size+=i["b"]
                    baseurl=info["data"]["vp"]["du"].split("/")
                    baseurl.insert(-1,key)
                    url="/".join(baseurl)+vlink+'?su='+gen_uid+'&qyid='+uuid4().hex+'&client=&z=&bt=&ct=&tn='+str(randint(10000,20000))
                    urls.append(JsonResource(url,headers=self.headers).get_resource()["l"])
                #download should be complete in 10 minutes
                #because the url is generated before start downloading
                #and the key may be expired after 10 minutes
                # print title
                data[bid_name] = urls
                data[bid_name+'_size'] = size
                # if not info_only:
                #     download_urls(urls, title, 'flv', size, output_dir = output_dir, merge = merge)

            bid_name = 'fullhd'
            if bid_name not in data:
                bid_name = 'suprt-high'
            if bid_name not in data:
                bid_name = 'high'
            if bid_name not in data:
                bid_name = 'standard'
            return data[bid_name]
        except Exception as e:
            traceback.print_stack()
            print e
            print tvid, videoid
            return None

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # print Iqiyi().parse_url('http://www.iqiyi.com/v_19rrhm6lw0.html')
    print Iqiyi().parse('425746500', '451993a1c186b1ae7e7f16c9a4537492')
