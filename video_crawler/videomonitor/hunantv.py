#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
from resource.http import HTMLResource, JsonResource

class Hunantv():
    name = "Hunantv (湖南台芒果TV)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.',
                'X-Requested-With': 'ShockwaveFlash/19.0.0.185',
                'Referer': 'http://i1.hunantv.com/ui/swf/player/v1225/main.swf'
                }

    def parse(self, vid):
        try:
            urls = []
            refer = 'http://player.hunantv.com/mango-tv3-main/MangoTV_3.swf?video_id=%s&skin_swf_url=http://player.hunantv.com/mango-tv3-skin/MangoTV_Skin_3.swf&player_swf_url=http://player.hunantv.com/mango-tv3-player/MangoTV_Player_3.swf&statistics_swf_url=http://player.hunantv.com/mango-tv3-statistics/MangoTV_Statistics_3.swf&mapd_swf_url=http://player.hunantv.com/mango-tv3-mapd/MangoTV_Mapd_3.swf&statistics_bigdata_bid=1' % vid
            self.headers['Referer'] = refer
            url = 'http://v.api.hunantv.com/player/video?video_id=%s&r=16158103439364' % vid
            content = JsonResource(url, headers=self.headers).get_resource()
            # 500 "该视频已经被下线 不能播放"
            if content['status'] == 200:
                video_types = [u'超清', u'高清', u'标清']
                video_info = content['data']['stream'][-1]
                video_infos = {}
                for v in content['data']['stream']:
                    video_infos[v['name']] = v
                for video_type in video_types:
                    if video_type in video_infos:
                        video_info = video_infos[video_type]
                        break
                url = video_info['url']
                cdn_content = JsonResource(url, headers=self.headers).get_resource()
                cdn_url = cdn_content['info']
                if 'playlist.m3u8' in cdn_url:
                    # http://221.204.195.24/mp4/2015/dianshiju/mrxx_35481/6A127070D8D57CDF68EC8577A63A6624_20151014_1_1_1102.mp4/playlist.m3u8?uuid=ef4d52080b1a4c538758804de3c6ed79&t=561fd670&win=3600&pno=1000&srgid=9&urgid=8&srgids=9&nid=858&payload=usertoken%3duuid%3def4d52080b1a4c538758804de3c6ed79%5eruip%3d3396079344%5ehit%3d1&rdur=21600&arange=0&limitrate=1614&fid=6A127070D8D57CDF68EC8577A63A6624&sign=95ece8dd3b24089a23407aff5dbdc288&ver=0x03&signnp=04576136479eaf4dfde228c52fcb9547
                    m3u8_content = HTMLResource(cdn_url, headers=self.headers).get_resource()
                    cdn_url_base = cdn_url[0: cdn_url.rfind('/')+1]
                    for m3u8 in m3u8_content.split('\n'):
                        if not m3u8.startswith('#'):
                            urls.append(cdn_url_base+m3u8)
                else:
                    urls.append(cdn_url)
                if len(urls) > 0:
                    return urls
            else:
                status = int(content['status'])
                if status > 0:
                    status = -1*status
                return str(status)
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-101'

    def get_headers(self):
        return self.headers

# http://www.hunantv.com/v/2/103886/f/2954553.html
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    urls = Hunantv().parse('2962751')
    print urls
    urls = Hunantv().parse('1837903')
    print urls
