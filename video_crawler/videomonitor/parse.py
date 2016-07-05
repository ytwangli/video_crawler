#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import simplejson
from resource.http import HTMLResource, JsonResource
from urllib2 import quote

class Parse():
    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/537.36',
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }

    # 360急速浏览器 super high normal
    # http://vpmadrid.flvcd.com/parsev.php?url=http%3a%2f%2fv.pptv.com%2fshow%2fm8kRjvZczApt61M.html&format=super
    # 视频头条APP
    # http://vpkb.flvcd.com/remote/parse_kuaibo_new.php?url=http%3a%2f%2fv.pptv.com%2fshow%2fm8kRjvZczApt61M.html&format=high
    # format super normal high super, ext mp4 m3u8 flv,
    # http://jxs.s.yunfan.com/remote/parse_kuaibo_new.php?url=http%3A%2F%2Fwww.iqiyi.com%2Fv_19rrlcjvk0.html&format=normal&ext=m3u8
    #
    # 废弃
    # http://vpsky.flvcd.com/yotian.php?url=http://v.pptv.com/show/m8kRjvZczApt61M.html
    # http://vpsky.flvcd.com/yotian_m3u8.php?url=http://v.pptv.com/show/m8kRjvZczApt61M.html
    #
    # 网页
    # http://www3.flvcd.com/parse.php?kw=http://v.pptv.com/show/m8kRjvZczApt61M.html
    #
    # 客户端返回
    # http://www2.flvcd.com/interface/parsem-flvcd.php?url=http://v.pptv.com/show/m8kRjvZczApt61M.html&format=super

    def parse_flvcd(self, url):
        try:
            flvcd_url = 'http://jxs.s.yunfan.com/remote/parse_kuaibo_new.php?url=%s&format=normal&ext=mp4' % quote(url, safe='')
            print flvcd_url
            content =JsonResource(flvcd_url, headers=self.headers).get_resource()
            print content
        except Exception as e:
            traceback.print_stack()
            print e
            print url
        return '-101'


    def parse(self, site, vid, sid):
        try:
            if site == 'pptv':
                url = 'http://v.pptv.com/show/%s.html' % sid
                self.parse_flvcd('http://tv.sohu.com/20151013/n423159957.shtml')
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-100'

    def get_headers(self):
        return self.headers

# http://vv.video.qq.com/gethls?vid=l0178727rkf&otype=xml&format=2
# http://cache.tv.qq.com/qqplayerout.swf?vid=

# http://www.wasu.cn/Play/show/id/4364488
# http://www.wasu.cn/wap/Play/show/id/4364488
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Parse().parse('pptv', '24425825', 'YRLJRq4UhMIlows')