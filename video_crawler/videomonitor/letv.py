#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import traceback
import random
import time
from resource.http import HTMLResource, JsonResource

class Letv():
    name = "乐视 (Letv)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
                }

    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
                }

    def get_timestamp(self):
        tn = random.random()
        url = 'http://api.letv.com/time?tn={}'.format(tn)
        content = JsonResource(url, headers=self.headers).get_resource()
        return content['stime']

    def get_key(self, t):
        for s in range(0, 8):
            e = 1 & t
            t >>= 1
            e <<= 31
            t += e
        return t ^ 185025305

    def calcTimeKey(self, t):
        ror = lambda val, r_bits, : ((val & (2**32-1)) >> r_bits%32) | (val << (32-(r_bits%32)) & (2**32-1))
        return ror(ror(t,773625421%13)^773625421,773625421%17)


    def decode(self, data):
        version = data[0:5]
        if version.lower() == b'vc_01':
            length = len(data)-5
            length_end = length-6
            data1 = [0]*length
            data2 = [0]*length
            i = 0
            while(i<length):
                data1[i] = ord(data[i+5])
                i += 1
            loc8 = [0]*12
            i = 0
            while(i<6):
                tmp1 = data1[length-6+i]
                if i>0:
                    loc8[2*i-1] = tmp1 >> 4
                loc8[2*i] = tmp1 & 15
                i += 1
            loc8[11] = data1[5] >> 4
            i = 0
            while(i<6):
                data2[i] = chr((loc8[2 * i] << 4) + loc8[2*i+1])
                i += 1
            i=0
            while(i<length_end):
                data2[i+6] = chr(((data1[i] & 15) << 4) + (data1[i+1] >> 4))
                i += 1
            return ''.join(data2)
            #get real m3u8
            # loc2 = data[5:]
            # length = len(loc2)
            # loc4 = [0]*(2*length)
            # # for i in range(length):
            # i=0
            # while(i<length):
            #     tmp1 = ord(loc2[i])
            #     loc4[2*i] = tmp1 >> 4
            #     loc4[2*i+1] = tmp1 & 15
            #     i += 1
            # loc6 = loc4[len(loc4)-11:] + loc4[:len(loc4)-11]
            # loc7 = [0]*length
            # i=0
            # while(i<length):
            #     loc7[i] = (loc6[2 * i] << 4) + loc6[2*i+1]
            #     i += 1
            # return ''.join([chr(i) for i in loc7])
        else:
            # directly return
            return data


    def video_info(self, vid):
        urls = []
        url = 'http://api.letv.com/mms/out/video/playJson?id={}&platid=1&splatid=101&format=1&tkey={}&domain=www.letv.com'.format(vid, self.calcTimeKey(int(time.time())))
        content = JsonResource(url, headers=self.headers).get_resource()
        if str(content['statuscode']) == '1001':
            if str(content['playstatus']['status']) == '0':
                return '-102'
            stream_id = None
            support_stream_id = content["playurl"]["dispatch"].keys()
            # print("Current Video Supports:")
            # for i in support_stream_id:
            #     print("\t--format",i,"<URL>")
            if "1080p" in support_stream_id:
                stream_id = '1080p'
            elif "720p" in support_stream_id:
                stream_id = '720p'
            else:
                stream_id =sorted(support_stream_id,key= lambda i: int(i[1:]))[-1]

            url2 =content["playurl"]["domain"][0]+content["playurl"]["dispatch"][stream_id][0]
            ext = content["playurl"]["dispatch"][stream_id][1].split('.')[-1]
            url2+="&ctv=pc&m3v=1&termid=1&format=1&hwtype=un&ostype=Linux&tag=letv&sign=letv&expect=3&tn={}&pay=0&iscpn=f9051&rateid={}".format(random.random(),stream_id)

            content2 = JsonResource(url2, headers=self.pcheaders).get_resource()
            # hold on ! more things to do
            # to decode m3u8 (encoded)
            m3u8_url = content2["location"]
            print m3u8_url
            m3u8 = HTMLResource(m3u8_url, headers=self.pcheaders).get_resource()
            m3u8_list = self.decode(m3u8).split('\r\n')
            for m3u8 in m3u8_list:
                if m3u8.startswith('http://'):
                    urls.append(m3u8)
                if m3u8.startswith('#EXT-LETV-START-TIME:'):
                    start_time = float(m3u8.replace('#EXT-LETV-START-TIME:', ''))
                    if start_time > 120.00:
                        return urls
        # print m3u8_list
        # urls = re.findall(r'^[^#][^\r]*',m3u8_list,re.MULTILINE)
        # return ext,urls
            if len(urls) > 0:
                return urls
        return '-101'

    def parse(self, vid):
        try:
            urls = self.video_info(vid)
            return urls
            # if result == 'ok':
            #     video_urls = self.extract()
            # if self.password_protected:
            #     return 'pass'
            # elif len(video_urls) == 0:
            #     return 'down'
            # else:
            #     return video_urls[0]
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
        return '-100'

    def get_headers(self):
        return self.headers

# http://www.letv.com/ptv/vplay/24283876.html
# http://www.letv.com/ptv/vplay/23057978.html
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Letv().parse('23613703')