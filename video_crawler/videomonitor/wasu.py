#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import simplejson
from resource.http import HTMLResource, JsonResource

class Wasu():
    name = "华数 (Wasu)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
                'Referer' : 'http://www.wasu.cn/wap/Play/show/id/4364488'
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }

    def video_info(self, vid):
        url = 'http://www.wasu.cn/wap/Play/show/id/' + vid
        content = HTMLResource(url, headers=self.headers).get_resource()
        self.headers['Referer'] = url
        if content is not None:
            index = content.find("var videoInfo = {") + len("var videoInfo = ")
            if index > 50:
                videoInfo = content[index: content.find("};", index)+1]
                videoInfo = videoInfo.replace('\'', '"').replace('	', '')
                videoInfo = simplejson.loads(videoInfo)
                key = videoInfo['key']
                url = videoInfo['url']
                gvurl = 'http://www.wasu.cn/wap/Api/getVideoUrl/id/%s/key/%s/url/%s/type/txt' % (vid, key, url)
                gvcontent = HTMLResource(gvurl, headers=self.headers).get_resource()
                if gvcontent is not None and gvcontent.startswith('http'):
                    videourl = gvcontent + '?vid='+vid+'&cid=60&version=MIPlayer_V1.4.2'
                    return videourl
        return '-101'

    def parse(self, vid):
        try:
            urls = self.video_info(vid)
            return urls
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-100'

    def get_headers(self):
        return self.headers

# http://www.wasu.cn/Play/show/id/4364488
# http://www.wasu.cn/wap/Play/show/id/4364488
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Wasu().parse('4364488')