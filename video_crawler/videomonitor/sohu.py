#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
import traceback
import uuid
import time
from resource.http import HTMLResource, JsonResource

class Sohu():
    name = "搜狐 (Sohu)"

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
                'X-Requested-With': 'ShockwaveFlash/20.0.0.228',
                'Referer': 'http://tv.sohu.com/20151201/n429164826.shtml',
                }

    headers = { 'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.2.2; MiBOX1S Build/CADEV)',
            }

    video_types = [
        "url_original",
        "url_super",
        "url_high",
        "url_nor"
    ]

    # def real_url(self, host,vid,tvid,new,clipURL,ck):
    #     # url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ ck+'&vid='+str(vid)+'&uid='+str(int(time.time()*1000))+'&t='+str(random.random())+'&rb=1'
    #     url = 'http://'+host+'/cdnList?new='+new+'&vid='+str(vid)+'&uid='+str(int(time.time()*1000))+'&tvid='+str(tvid)+'&ch=tv&sz=1635_902&md='+ck+'&prod=flash&pt=1&uuid='+str(random.random())
    #     print url
    #     content = JsonResource(url, headers=self.pcheaders).get_resource()
    #     end_url = content['url']
    #     return end_url
    #
    # def video_info(self, vid):
    #     video_urls = []
    #     # http://hot.vrs.sohu.com/vrs_flash.action?vid=2665183&af=1&bw=5189&plid=9029710&uid=14483595842658874955&out=0&g=8&referer=http%3A//tv.sohu.com/20151201/n429164826.shtml&t=0.9008373497053981
    #     url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
    #     content = JsonResource(url, headers=self.pcheaders).get_resource()
    #     for qtyp in ["oriVid","superVid","highVid" ,"norVid","relativeId"]:
    #         hqvid = content['data'][qtyp]
    #         if hqvid != 0:
    #             # if hqvid != vid:
    #             #     video_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % hqvid
    #             #     content = JsonResource(video_url, headers=self.pcheaders).get_resource()
    #             host = content['allot']
    #             tvid = content['tvid']
    #             data = content['data']
    #             # prot = info['prot']
    #             # title = data['tvName']
    #             size = sum(data['clipsBytes'])
    #             for new,clip,ck, in zip(data['su'], data['clipsURL'], data['ck']):
    #                 clipURL = quote(clip)
    #                 video_urls.append(self.real_url(host,hqvid,tvid,new,clipURL,ck))
    #             if len(video_urls) > 0:
    #                 print size
    #                 return video_urls
    #     return '-2'

        # info = json.loads(get_decoded_html('http://my.tv.sohu.com/play/videonew.do?vid=%s&referer=http://my.tv.sohu.com' % vid))
        # host = info['allot']
        # prot = info['prot']
        # tvid = info['tvid']
        # urls = []
        # data = info['data']
        # title = data['tvName']
        # size = sum(map(int,data['clipsBytes']))
        # for new,clip,ck, in zip(data['su'], data['clipsURL'], data['ck']):
        #     clipURL = urlparse(clip).path
        #     urls.append(real_url(host,vid,tvid,new,clipURL,ck))


    def video_info(self, vid):
        urls = []
        try:
            url = 'http://api.tv.sohu.com/v4/video/info/%s.json?site=1&api_key=9854b2afa779e1a6bff1962447a09dbd&plat=6&partner=1&sver=5.1.2&poid=1&sysver=4.4.4' % vid
            print url
            content = JsonResource(url, headers=self.headers).get_resource()
            status = content['status']
            if status == 200:
                if len(urls) == 0:
                    for video_type in self.video_types:
                        if video_type+'_mp4' in content['data']:
                            url_strs = content['data'][video_type+'_mp4'].split(',')
                            for url_str in url_strs:
                                urls.append(url_str)
                if len(urls) == 0:
                    for video_type in self.video_types:
                        if video_type in content['data']:
                            m3u8_url = content['data'][video_type]
                            content = HTMLResource(m3u8_url, headers=self.headers).get_resource()
                            for line in content.split('\n'):
                                if not line.startswith('#'):
                                    urls.append(line)
                if len(urls) == 0:
                    if 'download_url' in content['data']:
                        download_url = content['data']['download_url']
                        if download_url is not None and download_url != '':
                            urls.append(download_url)
            else:
                return str(status)
        except Exception as e:
            print e
        urls1 = []
        for url in urls:
            if '&prod=app' not in url:
                url += '&prod=app'
            url += "&uid=" + str(uuid.uuid4()).replace('-', '').upper() + "&ca=3&pt=2&pg=1&qd=1&sver=5.1.2&cv=5.1.2"
            urls1.append(url)
        return urls1

    # def video_info(self, vid):
    #     urls = []
    #     try:
    #         url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
    #         content = JsonResource(url, headers=self.headers).get_resource()
    #         status = content['status']
    #         if status == 1:
    #             pid = str(content['pid'])
    #             uuid_str = str(uuid.uuid4()).replace('-', '').upper()
    #             for qtyp in ["oriVid","superVid","highVid" ,"norVid","relativeId"]:
    #                 if qtyp in content['data']:
    #                     t =  str(int(time.time()))
    # http://hot.vrs.sohu.com/ipad2752485_4663802625567_5963706.m3u8?plat=15&pt=6&prod=ott&pg=1&ch=v&qd=816
    #                     url = "http://hot.vrs.sohu.com/ipad" + str(content['data'][qtyp]) + "_" + t + "_" + pid + ".m3u8?pg=1&pt=5&cv=5.0.0&qd=282&uid=" + uuid_str + "&sver=5.0.0&plat=6&ca=3&prod=app"
    #                     url = "http://hot.vrs.sohu.com/ipad" + str(content['data'][qtyp]) + "_" + t + "_" + pid + ".m3u8?plat=15&pt=6&prod=ott&pg=1&ch=v&qd=816"
    #                     print url
    #         else:
    #             return str(status)
    #     except Exception as e:
    #         print e
    #     return urls

    def parse(self, vid):
        try:
            urls = self.video_info(vid)
            print urls
            return urls
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
            return 'error'

    def get_headers(self):
        return self.headers

# &prod=flash &prod=h5 &prod=app
# api_key = 9854b2afa779e1a6bff1962447a09dbd or 88a12cee7016fe81ac2ab686d918bc7c  f351515304020cad28c92f70f002261c
# add  &prod=app  add "&uid=" + UUID.randomUUID().toString().toUpperCase() + "&ca=3&pt=2&pg=1&qd=1&sver=5.1.2&cv=5.1.2";
# http://api.tv.sohu.com/v4/video/info/1384677.json?site=1&api_key=695fe827ffeb7d74260a813025970bd5&plat=3&partner=1&sver=3.5&poid=1&
# http://api.tv.sohu.com/v4/video/info/%s.json?site=1&api_key=%s&plat=6&partner=1&sver=5.1.2&poid=1&sysver=4.4.4&aid=%s  (vid, api_key, playlistId)
# http://hot.vrs.sohu.com/vrs_flash.action?vid=2400333
# http://hot.vrs.sohu.com/ipad2752485_4663802625567_5963706.m3u8?plat=15&pt=6&prod=ott&pg=1&ch=v&qd=816
# http://hot.vrs.sohu.com/ipad2637839_4663800395131_5848150.m3u8?plat=15&pt=6&prod=ott&pg=1&ch=v&qd=816
# http://data.vod.itc.cn/?new=/110/192/lPZQHwzlTJybTrvgKq5UcC.mp4&vid=2752485&plat=3&mkey=OaD4WPz0ZJoKUn9t-xa7sd3pYbmtFE64&ch=tv&prod=app
# http://tv.sohu.com/20151013/n423159957.shtml  vid=2637837  playlistId=9058326

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # 2400333
    urls = Sohu().parse('2637837')
    for url in urls:
        print url
    # if urls != '-2':
    #     HTMLResource('', headers=Sohu().get_headers()).download_video_ts(urls, 'D:\\sohu.mp4', 1024*1024*100)
