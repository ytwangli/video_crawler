#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import random
import re
import hashlib
from resource.http import HTMLResource, JsonResource

class Kankan():
    name = "KanKan (迅雷看看)"

    headers = { 'User-Agent': 'ozilla/5.0 (Linux; Android 4.2.2; GT-I9505 Build/JDQ39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
                'Referer': 'http://m.kankan.com/v/89/89228.shtml?new=1',
                'Cookie': 'KANKANWEBUID=49fc997048332e33b5204a67cf395fff; WEB_REF=; WAP_REF=http%253A%252F%252Fvod.kankan.com%252Fv%252F89%252F89228.shtml; KANKANWEBSESSIONID=b804ededfbca38f9d2694d049c0cc262; f_refer=http%253A%252F%252Fvod.kankan.com%252Fv%252F89%252F89228.shtml; Hm_lvt_f85580b78ebb540403fe1f04da080cfd=1453176544; Hm_lpvt_f85580b78ebb540403fe1f04da080cfd=1453176544',
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }

    def parse(self, vid):
        try:
            url = 'http://api.pad.kankan.com/api.php?movieid=%s&type=video&mod=detail&os=az&osver=4.4.4&productver=4.5.2.6' % vid
            content = JsonResource(url, headers=self.headers).get_resource()
            surl = content['flvs']['urls'][-1]['url_play']
            gcids = re.findall(r"http://.+?/.+?/(.+?)/", surl)
            gcid = gcids[-1]

            # info_url = 'http://p2s.cl.kankan.com/getCdnresource_flv?gcid=%s&bid=22' % gcid  # pc
            info_url = 'http://mp4.cl.kankan.com/getCdnresource_flv?gcid=%s' % gcid  # h5
            content = HTMLResource(info_url, headers=self.headers).get_resource()
            if '{ip:"' in content:
                ip = re.search(r'ip:"(.+?)"', content).group(1)
                port = re.search(r'port:(\d+)', content).group(1)
                path = re.search(r'path:"(.+?)"', content).group(1)
                param1 = re.search(r'param1:(\d+)', content).group(1)
                param2 = re.search(r'param2:(\d+)', content).group(1)
                m2 = hashlib.md5()
                # var d=hex_md5("xl_mp43651"+g.param1+g.param2);
                m2.update('xl_mp43651' + param1 + param2)
                key = m2.hexdigest()
                video_url = 'http://%s:80/%s?key=%s&key1=%s' % (ip, path, key, param2)
                return video_url
            else:
                return self.parse_h5(vid)
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-100'

    def parse_h5(self, vid):
        try:
            url = 'http://m.kankan.com/vod/%s/%s.shtml' % (int(vid)/1000, vid)
            content = HTMLResource(url, headers=self.headers).get_resource()
            if content is None:
                print url
                return '-600'
            surls = re.search(r'surls:\[\'.+?\'\]|lurl:\'.+?\.flv\'', content).group(0)
            gcids = re.findall(r"http://.+?/.+?/(.+?)/", surls)
            gcid = gcids[-1]

            info_url = 'http://mp4.cl.kankan.com/getCdnresource_flv?gcid=%s' % gcid
            content = HTMLResource(info_url, headers=self.headers).get_resource()
            ip = re.search(r'ip:"(.+?)"', content).group(1)
            port = re.search(r'port:(\d+)', content).group(1)
            path = re.search(r'path:"(.+?)"', content).group(1)
            param1 = re.search(r'param1:(\d+)', content).group(1)
            param2 = re.search(r'param2:(\d+)', content).group(1)
            m2 = hashlib.md5()
            # var d=hex_md5("xl_mp43651"+g.param1+g.param2);
            m2.update('xl_mp43651' + param1 + param2)
            key = m2.hexdigest()
            video_url = 'http://%s:80/%s?key=%s&key1=%s' % (ip, path, key, param2)
            return video_url
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-101'

    def get_headers(self):
        return self.headers

# http://vod.kankan.com/v/89/89228.shtml
# 102  http://video.kankan.com/news/vod/70/70045.shtml
# 101  http://yule.kankan.com/vod/72/72801.shtml
# 100  http://video.kankan.com/news/vod/73/73293.shtml
# 100  http://sc.kankan.com/vod/392/392970.shtml
# 100  http://video.kankan.com/news/vod/392/392970.shtml
# http://182.118.14.147:80//data11/cdn_transfer/72/E8/72f04029d8532193a39baecaee60a567e8ff44e8.mp4?key=82d710917a14eb51d7b6945a79f023eb&key1=1453188777
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # urls = Kankan().parser('24096559')
    # urls = Kankan().parse('89228')
    # print urls
    urls = Kankan().parse('76090')
    print urls