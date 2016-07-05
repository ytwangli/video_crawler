#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import simplejson
from resource.http import HTMLResource, JsonResource

class Baofeng():
    name = "暴风影音 (Baofeng)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.2; GT-I9505 Build/JDQ39) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
                'Referer': 'http://www.baofeng.com/play/159/play-793159.html'
                }

    ipmap = {
        'b': "0",
        'a': "1",
        'o': "2",
        'f': "3",
        'e': "4",
        'n': "5",
        'g': "6",
        'h': "7",
        't': "8",
        'm': "9",
        'l': ".",
        'c': "A",
        'p': "B",
        'z': "C",
        'r': "D",
        'y': "E",
        's': "F"
    }

    def parse(self, vid):
        try:
            urls = []
            # <script type="text/javascript">var movie_detail = {"info_channel":"1","info_complatestatus":0,"info_pianyuan":[{"aid":"144568","hd_type":"480P","wid":"13","left_eye":0,"exclusive":0,"dzone":1,"ispay":0,"3d":0,"pay_type":0,"type":1}],"info_id":"790464","info_wid":"13"}</script>
            url = 'http://m.hd.baofeng.com/play/%s/play-%s.html' % (int(vid) % 1000, vid)
            self.headers['Referer'] = url
            content = HTMLResource(url, headers=self.headers).get_resource()
            index = content.find('<script type="text/javascript">var movie_detail = ')+len('<script type="text/javascript">var movie_detail = ')
            content = content[index: content.find('</script>', index)]
            json_content = simplejson.loads(content)
            if 'info_id' not in json_content or json_content['info_id'] is None:
                url = 'http://iphone.shouji.baofeng.com/iphone/minfo/*/%s/%s_1.json?mtype=normal&ver=3.2.1&type=1&g=23&td=0' % (int(vid) % 1000, vid)
                content = JsonResource(url, headers=self.headers).get_resource()
                if 'status' in content and content['reason'] == 'No Video Found':
                    return '-103'
                video_data = content['video_list'][0]
                if 'bf-' not in video_data['site']:
                    return '-104'
                page_url = video_data['page_url']
                content = HTMLResource(page_url, headers=self.headers).get_resource()
                if '<title>手机暴风影音，手机万能播放器免费下载，万能，高清，流畅，省电。</title>' in content:
                    return '-102'
                index = content.find('"text/javascript">var static_storm_json = ')+len('"text/javascript">var static_storm_json = ')
                content = content[index: content.find(';var recommended_json = [', index)]
                json_content = simplejson.loads(content)
                iid = json_content['iid']
                size = json_content['size']
            else:
                aid = int(json_content['info_pianyuan'][0]['aid'])
                wid = int(json_content['info_pianyuan'][0]['wid'])
                url = 'http://minfo.baofeng.net/asp_c/%s/%s/%s-n-%s-r-1-s-%s-p-%s.json?callback=_callbacks_._1ihq1mimm' % (wid, aid%500, aid, 50, 0, 1)
                content = HTMLResource(url, headers=self.headers).get_resource().replace('_callbacks_._1ihq1mimm(', '').rstrip(')')
                json_content = simplejson.loads(content)
                iid = json_content['video_list'][0]['iid']
                size = json_content['video_list'][0]['size']
            url = 'http://rd.p2p.baofeng.net/queryvp.php?type=3&gcid=' + iid +'&callback=_callbacks_._2ihq0vso1'
            content = HTMLResource(url, headers=self.headers).get_resource().replace('_callbacks_._2ihq0vso1(', '').rstrip(')').replace('\'', '"')
            json_content = simplejson.loads(content)
            # {'err':'0','ip':'aoflafalagnlgh,aamlattlholaft,ooalofglahelagf','port':'80','path':'mppzfetgbamhhecbpgehonaothrbcatbmgeefpma','key':'B487D0C0BCFC13F6156779C175C601BC'}
            ips = json_content['ip'].split(',')
            for ip in ips:
                result_ip = ''
                # print len(ip)
                for i in xrange(0, len(ip)):
                    result_ip += self.ipmap[ip[i]]
                url = 'http://%s:%s/%s?key=%s&filelen=%s' % (result_ip, json_content['port'], json_content['path'], json_content['key'], size)
                urls.append(url)
            if len(urls) > 0:
                return urls
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-100'


    def get_headers(self):
        return self.headers

# http://www.baofeng.com/play/173/play-3473173.html
# http://www.baofeng.com/play/159/play-793159.html
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # url = Baofeng().parse('790464')
    # url = Baofeng().parse('10354753')
    url = Baofeng().parse('11220877')
    print url
    # http://m.hd.baofeng.com/video/413/video-37-2561913.html  "vid": "2561913",  "img_url": "/vimg/wid/37/413/2561913/52_127216243_128*96.jpg",
    # 10354753  9-8lol JY 削弱不了依旧最强ap沙皇教你后期致霸