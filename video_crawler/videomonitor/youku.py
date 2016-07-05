#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
import re
import base64
import time
import urllib
import traceback
from resource.http import HTMLResource, JsonResource

class Youku():
    name = "优酷 (Youku)"

    headers = { 'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; en-us; Nexus 5 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Mobile Safari/537.36',
                'Referer': 'http://static.youku.com/'
                }
    pcheaders = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
                }
    stream_types = [
        {'id': 'mp4hd3', 'alias-of' : 'hd3'},
        {'id': 'hd3',    'container': 'flv', 'video_profile': '1080P'},
        {'id': 'mp4hd2', 'alias-of' : 'hd2'},
        {'id': 'hd2',    'container': 'flv', 'video_profile': '超清'},
        {'id': 'mp4hd',  'alias-of' : 'mp4'},
        {'id': 'mp4',    'container': 'mp4', 'video_profile': '高清'},
        {'id': 'flvhd',  'container': 'flv', 'video_profile': '标清'},
        {'id': 'flv',    'container': 'flv', 'video_profile': '标清'},
        {'id': '3gphd',  'container': '3gp', 'video_profile': '标清（3GP）'},
    ]
    stream_order = ['mp4hd3', 'hd3', 'mp4hd2', 'hd2', 'mp4hd', 'mp4', 'flvhd', 'flv', '3gphd']
    f_code_1 = 'becaf9be'
    f_code_2 = 'bf7e5f01'
    cookie = ''
    request = None
    password_protected = False

    def trans_e(self, a, c):
        f = h = 0
        b = list(range(256))
        result = ''
        while h < 256:
            f = (f + b[h] + ord(a[h % len(a)])) % 256
            b[h], b[f] = b[f], b[h]
            h += 1
        q = f = h = 0
        while q < len(c):
            h = (h + 1) % 256
            f = (f + b[h]) % 256
            b[h], b[f] = b[f], b[h]
            if isinstance(c[q], int):
                result += chr(c[q] ^ b[(b[h] + b[f]) % 256])
            else:
                result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
            q += 1
        return result

    def generate_ep(self, no, streamfileids, sid, token):
        number = hex(int(str(no), 10))[2:].upper()
        if len(number) == 1:
            number = '0' + number
        fileid = streamfileids[0:8] + number + streamfileids[10:]
        ep = self.trans_e(self.f_code_2, sid + '_' + fileid + '_' + token)
        ep = urllib.quote(base64.b64encode(ep), safe='~()*!.\'')
        return fileid, ep

    # Obsolete -- used to parse m3u8 on pl.youku.com

    def parse_m3u8(self, m3u8):
        return re.findall(r'(http://[^?]+)\?ts_start=0', m3u8)


    def prepare(self, vid):
        self.vid = vid
        self.streams = {}
        # Hot-plug cookie handler
        # ssl_context = request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        # cookie_handler = request.HTTPCookieProcessor()
        # opener = request.build_opener(ssl_context, cookie_handler)
        # opener.addheaders = [('Cookie','r={}'.format(time.time()))]
        # request.install_opener(opener)

        api_url = 'http://play.youku.com/play/get.json?vid=%s&ct=12' % self.vid
        api_url1 = 'http://play.youku.com/play/get.json?vid=%s&ct=10' % self.vid
        data = None
        data1 = None
        try:
            # self.headers['Cookie'] = '__ysuid={}'.format(time.time())
            self.headers['Cookie'] = '__ali=1452590907892F3A; ykss=3ec79456d6e8c3ec2730c93a; msgid_58=58; __ysuid='+str(time.time()*1000)+'Qrb7os; __aliCount=1; premium_cps_vid=XMTQ0MjQyODA0OA%3D%3D; xreferrer=; r="8MaZyz7N+UYvw0SPC+D/SzXMnaMxlduh9hOeuwsu+Khn2Y4B6TT+zQOLHBHwE+G/1/bvewNqLMJYBaWZ/cKl3YA9xxrap1EUuOwBoAHCDcqwpq/oNruqwjvzerTYg9XwsKMdGxpmfYsifqUD9aFPKGGY7+hxT4ReP+Pc+kW8om4=";'
            self.request = JsonResource(api_url, headers=self.headers)
            meta = self.request.get_resource()
            self.request.change(url = api_url1)
            meta1 = self.request.get_resource()
            self.cookie = self.request.get_cookie(need_request=False)
            data = meta['data']
            if 'error' in data:
                code = data['error']['code']
                if code not in [-100, -101, -102, -103, -104, -201, -202, -204, -307, -401, -501]:
                    print code
                    print data['error']['note']
                if code < 0:
                    return str(code)
            data1 = meta1['data']
            self.title = data['video']['title']
            self.ep = data['security']['encrypt_string']
            self.ip = data['security']['ip']
            if 'error' in data:
                code = data['error']['code']
                #-100该视频正在转码中......，请稍后  -101该视频正在审核中......，请稍后  -102该视频已被屏蔽，您可以尝试搜索操作。  -103该视频转码失败，请联系客服  -104视频不存在  -201该视频被设为私密，请联系上传者  -202该视频已经加密，请输入密码  -307观看此节目，请先登录！  -401抱歉，因版权原因无法观看此视频！  -501服务器发生致命错误
                if code not in [-100, -101, -102, -103, -104, -201, -202, -204, -205, -307, -401, -501]:
                    print code
                    print data['error']['note']
                if code < 0:
                    return str(code)
            if 'stream' not in data: # and self.password_protected
                print('[Failed] Wrong password.')
                return '-202'

            stream_types = dict([(i['id'], i) for i in self.stream_types])
            self.streams_parameter = {}
            self.streams_fallback_parameter = {}
            audio_lang = data1['stream'][0]['audio_lang']
            for stream in data1['stream']:
                stream_id = stream['stream_type']
                if stream_id in stream_types and stream['audio_lang'] == audio_lang:
                    if 'alias-of' in stream_types[stream_id]:
                        stream_id = stream_types[stream_id]['alias-of']
                    self.streams[stream_id] = {
                        'container': stream_types[stream_id]['container'],
                        'video_profile': stream_types[stream_id]['video_profile'],
                        'size': stream['size']
                    }
                    self.streams_parameter[stream_id] = {
                        'fileid': stream['stream_fileid'],
                        'segs': stream['segs']
                    }

            for stream in data['stream']:
                stream_id = stream['stream_type']
                if stream_id in stream_types and stream['audio_lang'] == audio_lang:
                    if 'alias-of' in stream_types[stream_id]:
                        stream_id = stream_types[stream_id]['alias-of']
                    self.streams_fallback_parameter[stream_id] = {
                        'fileid': stream['stream_fileid'],
                        'segs': stream['segs']
                    }
            # Audio languages
            if 'dvd' in data and 'audiolang' in data['dvd']:
                self.audiolang = data['dvd']['audiolang']
                for i in self.audiolang:
                    i['url'] = 'http://v.youku.com/v_show/id_{}'.format(i['vid'])
            return 'ok'
        except AssertionError:
            print('[Failed] Video not found.')
            return '-2'
        except Exception as e:
            print e
            traceback.print_stack()


    def get_stream_id(self):
        for stream_id in self.stream_order:
            if stream_id in self.streams:
                return stream_id

    def extract(self, stream_id=None):
        if stream_id is None:
            stream_id = self.get_stream_id()

        e_code = self.trans_e(
            self.f_code_1,
            base64.b64decode(bytes(self.ep))) #, 'ascii'
        sid, token = e_code.split('_')

        sp = self.streams_parameter
        while True:
            try:
                segs = sp[stream_id]['segs']
                streamfileid = sp[stream_id]['fileid']

                urls = []
                if segs is None:
                    print 'error'
                for no in range(0, len(segs)):
                    k = segs[no]['key']
                    fileid, ep = self.generate_ep(no, streamfileid, sid, token)
                    q = urllib.urlencode(dict(
                        ctype = 12,
                        ev    = 1,
                        K     = k,
                        ep    = urllib.unquote(ep),
                        oip   = str(self.ip),
                        token = token,
                        yxon  = 1
                    ))
                    url = 'http://k.youku.com/player/getFlvPath/sid/{sid}_00' \
                        '/st/{container}/fileid/{fileid}?{q}'.format(
                        sid       = sid,
                        container = self.streams[stream_id]['container'],
                        fileid    = fileid,
                        q         = q
                    )
                    self.request.change(url = url)
                    content = self.request.get_resource()
                    if content is None:
                        if len(urls) > 0:
                            return urls
                        else:
                            print 'Error: '+str(self.vid)
                            return '0'
                    urls.extend([data['server'] for data in content])
                return urls
            except Exception as e:
                print e
                print self.vid
                traceback.print_stack()
                # Use fallback stream data in case of HTTP 404
                sp = self.streams_fallback_parameter


    def parse(self, vid):
        try:
            code = self.prepare(vid)
            if code == 'ok':
                video_urls = self.extract()
                if len(video_urls) == 0:
                    return '-3'
                else:
                    return video_urls[0]
            else:
                return code
        except Exception as e:
            traceback.print_stack()
            print e
            print vid
            return '-2'

    def get_headers(self):
        return self.pcheaders

# http://v.youku.com/v_show/id_XMTM1ODgzMjA4OA==_ev_1.html
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    print Youku().parse('357298735')