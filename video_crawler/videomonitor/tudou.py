#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
from resource.http import HTMLResource, JsonResource

class Tudou():
    name = "土豆 (Tudou)"
    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:44.0) Gecko/20100101 Firefox/44.0',
                  'Referer': 'http://js.tudouui.com/bin/lingtong/PortalPlayer_189.swf',
                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }

    def parse(self, vid):
        try:
            base_url = 'http://api.3g.tudou.com/v4/play/detail?pid=7b979ca489bcc36e&_t_=1435643508&_e_=md5&guid=4c49c456777e2bb7a2fc27d7260d96be&ver=4.0&network=WIFI&show_playlist=1&iid='+vid
            content = JsonResource(base_url, self.pcheaders).get_resource()
            if content is not None:
                if content.get('status', '') == 'failed':
                    return '-4'
                data = content.get('detail', {})
                item_media_type = data.get('item_media_type', '')
                if item_media_type == '音频':
                    return '-1'
            video_info = JsonResource('http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s' % vid, headers=self.pcheaders).get_resource()
            data = video_info.get('3', video_info.get('4', video_info.get('2', video_info.get('5', None))))
            if data is not None and 'size' in data[0]:
                video_url = HTMLResource('http://ct.v2.tudou.com/f?id=%s' % data[0]['k'], headers=self.pcheaders).get_resource()
                if '<e 'in video_url and 'error=' in video_url:
                    data = video_info.get('52', None)
                    if data is not None and 'size' in data[0]:
                        video_url = HTMLResource('http://ct.v2.tudou.com/f?id=%s' % data[0]['k'], headers=self.pcheaders).get_resource()
                        if '<e 'in video_url and 'error=' in video_url:
                            return '-3'
                video_url_cdn = video_url[video_url.find('>')+1: video_url.find('</f>')].replace('&amp;', '&')
                if video_url_cdn.startswith('http://'):
                    return video_url_cdn
                else:
                    return '-3'
            return '-2'
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
            return '-3'

    def get_headers(self):
        return self.pcheaders

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Tudou().parse('232303404')