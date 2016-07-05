#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import time
from resource.http import HTMLResource, JsonResource

class Funtv():
    name = "风行 (Funtv)"
    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.',
                'X-Requested-With': 'ShockwaveFlash/19.0.0.185',
                'Referer': 'http://www.fun.tv/vplay/v-232303404/'
                }

    def parse(self, vid):
        try:
            self.headers['Referer'] = 'http://www.fun.tv/vplay/v-%s/' % vid
            # http://pv.funshion.com/v5/video/play/?id=4225246&cl=aphone&uc=5
            content = JsonResource('http://api1.fun.tv/ajax/playinfo/video/%s/' % vid, headers=self.headers).get_resource()
            video_types = ['sdvd', 'hd', 'dvd', 'tv']
            if 'videoid' not in content['data'] or 'files' not in content['data']:
                return '-102'
            video_info = content['data']['files'][-1]
            video_infos = {}
            for v in content['data']['files']:
                video_infos[v['clarity']] = v
            for video_type in video_types:
                if video_type in video_infos:
                    video_info = video_infos[video_type]
                    break
            url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json?file=%s&clifz=fun&mac=&tm=%s' % (video_info['hashid'], video_info['filename'], int(time.time()))
            cdn_content = JsonResource(url, headers=self.headers).get_resource()
            urls = []
            for playlist in cdn_content['playlist']:
                urls.append(playlist['urls'][0])
            if len(urls) > 0:
                return urls
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-101'

    def get_headers(self):
        return self.headers

# http://www.fun.tv/vplay/v-232303404/
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Funtv().parse('3850199')