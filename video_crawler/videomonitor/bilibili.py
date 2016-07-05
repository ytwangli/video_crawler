#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import random
import re
import gzip
import json
import zlib
import urllib
import hashlib
from resource.http import HTMLResource, JsonResource

class Bilibili():
    name = "Bilibili (Bilibili)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.2; GT-I9505 Build/JDQ39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
                'Referer': 'http://player.aplus.pptv.com/corporate/proxy/proxy.html'
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }
    # USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36'
    # APPKEY = '85eb6835b0a1034e'
    # APPSEC = '2ad42749773c441109bdc0191257a664'
    # APPKEY2 = '95acd7f6cc3392f3'
    #
    # def GetSign(self,params,appkey,AppSecret=None):
    #     params['appkey']=appkey
    #     data = ""
    #     paras = sorted(params)
    #     paras.sort()
    #     for para in paras:
    #         if data != "":
    #             data += "&"
    #         data += para + "=" + str(params[para])
    #     if AppSecret == None:
    #         return data
    #     m = hashlib.md5()
    #     m.update((data+AppSecret).encode('utf-8'))
    #     return data+'&sign='+m.hexdigest()
    #
    # def ChangeFuck(self, params):
    #     data = ""
    #     paras = params
    #     for para in paras:
    #         if data != "":
    #             data += "&"
    #         data += para + "=" + str(params[para])
    #     return data
    #
    # def urlfetch(self, url):
    #     ip = random.randint(1,255)
    #     select = random.randint(1,2)
    #     if select == 1:
    #         ip = '220.181.111.' + str(ip)
    #     else:
    #         ip = '59.152.193.' + str(ip)
    #     req_headers = {'Accept-Encoding': 'gzip, deflate', 'User-Agent': self.USER_AGENT, 'Client-IP': ip, 'X-Forwarded-For': ip, 'Cookie': 'DedeUserID=8926815; DedeUserID__ckMd5=7a15e38c8988dd51; SESSDATA=f3723f8c%2C1445522963%2Ce07d220f;'}
    #     content = HTMLResource(url, headers=req_headers).get_resource()
    #     # elif content_encoding == 'deflate':
    #     #     decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)
    #     #     data = decompressobj.decompress(response.read())+decompressobj.flush()
    #     return content


    # def parse(self, sid, pid=1):
    #     urls = []
    #     try:
    #         overseas=False
    #         url_get_media = 'http://interface.bilibili.com/playurl?' if not overseas else 'http://interface.bilibili.com/v_cdn_play?'
    #         cid_args = {'type': 'json', 'id': sid, 'page': pid}
    #
    #         resp_cid = self.urlfetch('http://api.bilibili.com/view?'+self.GetSign(cid_args,self.APPKEY,self.APPSEC))
    #         resp_cid = dict(json.loads(resp_cid.decode('utf-8', 'replace')))
    #         if 'error' in resp_cid:
    #             return str(resp_cid['code'])
    #         cid = resp_cid.get('cid')
    #         AppkeyChoices = [self.APPKEY, self.APPKEY2]
    #         APPKEYF = random.choice(AppkeyChoices)
    #         media_args = {'otype': 'json', 'cid': cid, 'type': 'flv', 'quality': 4, 'appkey': APPKEYF}
    #         resp_media = self.urlfetch(url_get_media+self.ChangeFuck(media_args))
    #         resp_media = dict(json.loads(resp_media.decode('utf-8', 'replace')))
    #         result = resp_media.get('result')
    #         if (result is 'error'):
    #             if 'code' in resp_media:
    #                 return resp_media['code']
    #             return '-999'
    #         media_urls = resp_media.get('durl')
    #         for media_url in media_urls:
    #             urls.append(media_url.get('url'))
    #     except Exception as e:
    #         traceback.print_stack()
    #         print e
    #     if len(urls) > 0:
    #         return urls[0]
    #     else:
    #         return -998


    def parse(self, cid):
        urls = []
        try:
            url = 'http://interface.bilibili.com/playurl?appkey=95acd7f6cc3392f3&quality=3&otype=json&type=flv&cid=%s' % (cid)
            content = JsonResource(url, self.headers).get_resource()
            if content is None:
                content = JsonResource(url, self.headers).get_resource()
            if content is not None and 'durl' in content:
                durls = content['durl']
                if type(durls)==list:
                    for durl in durls:
                        video_url = durl.get('url', '')
                        if video_url == '':
                            video_url = durl['backup_url'][-1]
                        urls.append(video_url)
        except Exception as e:
            traceback.print_stack()
            print e
        if len(urls) > 0:
            return urls
        else:
            return '-100'

    def get_headers(self):
        return self.headers

# id 纯主键
# sid 剧集  # http://www.bilibili.com/video/av sid /
# cid 子集、视频id
# http://www.bilibili.com/video/av3146859/
# http://www.bilibili.com/video/av2380003/
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    urls = Bilibili().parse('5784858')
    print urls
