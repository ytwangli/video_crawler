#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import simplejson
from resource.http import HTMLResource, JsonResource

class Acfun():
    name = "Acfun (Acfun)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.2; GT-I9505 Build/JDQ39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
                'Origin': 'http://m.acfun.tv',
                'deviceType': '2',
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }

    video_types = {
        1: '标清',
        2: '高清',
        3: '超清',
        4: '原画',
    }

    def parse(self, cid):
        try:
            url = 'http://api.aixifan.com/plays/%s/realSource' % cid
            content = JsonResource(url, headers=self.headers).get_resource()
            if content['code'] == 200:
                sourceType = content['data']['source']
                if sourceType == 'zhuzhan':
                    video_url = content['data']['files'][-1]['url']
                    return video_url
                elif sourceType == 'letv':
                    video_url = content['data']['files'][-1]['url']
                    return video_url
                else:
                    return '-105'
            else:
                return '-101'

            # url = 'http://www.acfun.tv/video/getVideo.aspx?id=2905592' + cid
            # content = JsonResource(url, headers=self.headers).get_resource()
            # sourceType = content['sourceType']
            # if sourceType == 'letv':
            #     if 'sourceId' in content:
            #         sourceId = content['sourceId']
            #         # letvcloud_download_by_vu(sourceId, '2d8c027396')
            # elif sourceType == 'zhuzhan':
            #     videoList = content['videoList']
            #     playUrl = videoList[-1]['playUrl']
            #     print playUrl
        except Exception as e:
            traceback.print_stack()
            print e
            print cid
        return '-100'

    def get_headers(self):
        return self.headers
# http://www.acfun.tv/video/getVideo.aspx?id=2848361
# http://acfunfix.sinaapp.com/?vid=2318907
# http://acfun.tudou.com/
# http://www.acfun.tv/v/ac2364832
# video_cid
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    urls = Acfun().parse('2185550')
    print urls
    urls = Acfun().parse('2364832')
    print urls
