#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import urllib2
import simplejson
import StringIO
import gzip
import xmltodict
import traceback
import os

class RedirctHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        pass
    def http_error_302(self, req, fp, code, msg, headers):
        pass

class HttpResource(object):
    """网络中的一个资源
    """
    def __init__(self, url, headers=None, proxies=None, timeout=60, max_retry_count=3, data=None):
        self.retry_count = 0
        self.url = url
        self.proxies = proxies
        #self.user_agent = user_agent
        self.timeout = timeout
        self.max_retry_count = max_retry_count
        self.cookie = None
        #if headers is None:
        #    self.headers = {'User-Agent': user_agent}
        self.headers = headers
        self.data = data

    def change(self, url=None):
        if url is not None:
            self.url = url

    def get_resource(self):
        content = self.__get_http_content()
        resource = self.parse(content)
        if resource is not None:
            return resource
        elif self.retry_count < self.max_retry_count:
            self.retry_count += 1
            # time.sleep(0.1)  # random.choice(range(self.retry_count))
            return self.get_resource()
        return None

    def get_cookie(self, need_request=True):
        if need_request:
            content = self.__get_http_content()
        return self.cookie

    def get_Location(self):
        response = None
        try:
            if self.data is None:
                request = urllib2.Request(self.url, headers=self.headers)
            else:
                request = urllib2.Request(self.url, self.data, headers=self.headers)
            if self.proxies is not None:
                request.set_proxy(self.proxies, 'http')
            debug_handler = urllib2.HTTPHandler() # debuglevel = 1
            opener = urllib2.build_opener(debug_handler, RedirctHandler)
            response = opener.open(request,timeout=self.timeout)
            # response = urllib2.urlopen(request, timeout=self.timeout)
            if 'Location' in response.headers:
                return response.headers['Location']
            # return self.url
            return response.url
        except urllib2.URLError as e:
            if hasattr(e, 'code'):
                code = e.code
                location = ''
                if (code in (301, 302, 303, 307)):
                    if 'Location' in e.headers:
                        location = e.headers['Location']
                        return location
                if code == 404:
                    return code
            if hasattr(e, 'filename'):
                return e.filename
            if hasattr(e, 'url'):
                return e.url
            elif hasattr(e, 'reason'):
                error_info = e.reason
            traceback.print_stack()
            print e
            #if self.url == e.url and e.code != 404:
            #    logging.warning('network error: %s, %s' % (self.proxies, self.url))
            return error_info


    def get_length(self):
        return self.download_mp4(None, get_length=True)

    def download_mp4(self, filepath, total_length=None, etag=None, last_size=None, outf=None, get_length=False):
        try:
            size = 0
            # if last_size is not None:
            #     # start from 0
            #     size = last_size
            #     self.headers['Range'] = 'bytes=%s-%s' % (last_size, total_length-1)
            # if etag is not None:
            #     self.headers['If-Range'] = etag
            if self.data is None:
                request = urllib2.Request(self.url, headers=self.headers)
            else:
                request = urllib2.Request(self.url, self.data, headers=self.headers)
            if self.proxies is not None:
                request.set_proxy(self.proxies, 'http')
            if self.cookie is not None:
                request.add_header('Cookie', self.cookie)
            response = urllib2.urlopen(request, timeout=self.timeout)
            if total_length is None:
                total_length = int(response.headers.get('Content-Length', 0))
                if get_length:
                    return total_length
            # etag = response.headers.get('ETag', '')
            # 以临时文件方式创建
            if outf is None:
                outf = open(filepath+'.tmp', 'wb')
            while True:
                data = response.read(10485760)  # 每次读取10MB
                data_len = len(data)
                if data_len == 0:
                    break
                outf.write(data)
                outf.flush()
                size += data_len
            if size != total_length:
                print (total_length, size)
                if self.retry_count < self.max_retry_count:
                    self.retry_count += 1
                    # return self.download_mp4(filepath, total_length, etag, size, outf, False)
                    return self.download_mp4(filepath)
                else:
                    outf.close()
                    os.remove(filepath+'.tmp')
                    return None
            else:
                # 下载完毕后改名
                outf.close()
                os.renames(filepath+'.tmp', filepath)
                return size
        except Exception as e:
            if self.retry_count < self.max_retry_count:
                self.retry_count += 1
                return self.download_mp4(filepath, get_length=get_length)
            if outf is not None:
                outf.close()
                os.remove(filepath+'.tmp')
            print e
            traceback.print_exc()
            print self.url
            return None


    def download_image(self, filepath):
        outf = None
        try:
            size = 0
            if self.data is None:
                request = urllib2.Request(self.url, headers=self.headers)
            else:
                request = urllib2.Request(self.url, self.data, headers=self.headers)
            if self.proxies is not None:
                request.set_proxy(self.proxies, 'http')
            if self.cookie is not None:
                request.add_header('Cookie', self.cookie)
            response = urllib2.urlopen(request, timeout=self.timeout)
            total_length = int(response.headers.get('Content-Length', 0))
            outf = open(filepath, 'wb')
            while True:
                data = response.read(102400)  # 每次读取100KB
                data_len = len(data)
                if data_len == 0:
                    break
                outf.write(data)
                outf.flush()
                size += data_len
            if size != total_length:
                print (total_length, size)
                if self.retry_count < self.max_retry_count:
                    self.retry_count += 1
                    # return self.download_mp4(filepath, total_length, etag, size, outf, False)
                    return self.download_image(filepath)
                else:
                    outf.close()
                    os.remove(filepath)
                    return None
            else:
                # 下载完毕后改名
                outf.close()
                return size
        except Exception as e:
            if self.retry_count < self.max_retry_count:
                self.retry_count += 1
                return self.download_image(filepath)
            if outf is not None:
                outf.close()
                os.remove(filepath)
            print e
            traceback.print_exc()
            print self.url
            return None

    def download_video(self, filepath, max_size=9999999999999):
        outf = None
        try:
            size = 0
            if self.data is None:
                request = urllib2.Request(self.url, headers=self.headers)
            else:
                request = urllib2.Request(self.url, self.data, headers=self.headers)
            if self.proxies is not None:
                request.set_proxy(self.proxies, 'http')
            if self.cookie is not None:
                request.add_header('Cookie', self.cookie)
            response = urllib2.urlopen(request, timeout=self.timeout)
            total_length = int(response.headers.get('Content-Length', 0))
            outf = open(filepath, 'wb')
            while True:
                data = response.read(102400)  # 每次读取100KB
                data_len = len(data)
                if data_len == 0:
                    break
                outf.write(data)
                outf.flush()
                size += data_len
                if size >= max_size:
                    break
            # if size != total_length and size < max_size:
            if False:
                print (total_length, size)
                if self.retry_count < self.max_retry_count:
                    self.retry_count += 1
                    return self.download_video(filepath, max_size)
                else:
                    outf.close()
                    os.remove(filepath)
                    return None
            else:
                # 下载完毕后改名
                outf.close()
                return size
        except Exception as e:
            if self.retry_count < self.max_retry_count:
                self.retry_count += 1
                return self.download_video(filepath, max_size)
            if outf is not None:
                outf.close()
                os.remove(filepath)
            print e
            traceback.print_exc()
            print self.url
            return None


    def download_video_ts(self, video_urls, filepath, max_size):
        outf = None
        size = 0
        try:
            total_size = 0
            outf = open(filepath, 'wb')
            for video_url in video_urls:
                if self.data is None:
                    request = urllib2.Request(video_url, headers=self.headers)
                else:
                    request = urllib2.Request(video_url, self.data, headers=self.headers)
                if self.proxies is not None:
                    request.set_proxy(self.proxies, 'http')
                if self.cookie is not None:
                    request.add_header('Cookie', self.cookie)
                response = urllib2.urlopen(request, timeout=self.timeout)
                total_length = int(response.headers.get('Content-Length', 0))
                total_size += total_length
                while True:
                    data = response.read(10240)  # 每次读取1MB  1048576
                    data_len = len(data)
                    if data_len == 0:
                        break
                    outf.write(data)
                    outf.flush()
                    size += data_len
                    if size >= max_size:
                        break
                if size >= max_size:
                    break
            outf.close()
            if size < 1024*1024*3:
                print (size, total_size, max_size)
                os.remove(filepath)
                print size
                if self.retry_count < self.max_retry_count:
                    self.retry_count += 1
                    return self.download_video_ts(video_urls, filepath, max_size)
                else:
                    return None
            else:
                # 下载完毕后改名
                return size
        except Exception as e:
            print e
            traceback.print_exc()
            print video_urls
            if outf is not None:
                outf.close()

            if size < 1024*1024*10:
                os.remove(filepath)
                if self.retry_count < self.max_retry_count:
                    self.retry_count += 1
                    return self.download_video_ts(video_urls, filepath, max_size)
            else:
                return size
            print filepath
            return None

    #子类重载函数
    def parse(self, content):
        return content

    @staticmethod
    def generate_url(base_url, params):
        return base_url + "&".join(['%s=%s' % (key, value) for key, value in params.iteritems()])

    def __get_http_content(self):
        try:
            if self.data is None:
                request = urllib2.Request(self.url, headers=self.headers)
            else:
                request = urllib2.Request(self.url, self.data, headers=self.headers)
            if self.proxies is not None:
                request.set_proxy(self.proxies, 'http')
            if self.cookie is not None:
                request.add_header('Cookie', self.cookie)
            response = urllib2.urlopen(request, timeout=self.timeout)

            if 'set-cookie' in response.headers:
                self.cookie = response.headers.get('set-cookie')
            if response.headers.get('content-length') == '0':
                self._print_log('no content')
                return None

            if response.headers.get('content-encoding') == 'gzip':
                return gzip.GzipFile(fileobj=StringIO.StringIO(response.read())).read()
            elif 'Content-Disposition' in response.headers and response.headers.get('Content-Disposition').endswith('.zip"'):
                return gzip.GzipFile(fileobj=StringIO.StringIO(response.read())).read()
            else:
                return response.read()
        except Exception as e:
            #if self.url == e.url and e.code != 404:
            #    logging.warning('network error: %s, %s' % (self.proxies, self.url))
            return None

    def _print_log(self, message):
        logging.warning('url:%s, response:%s' % (self.url, message))


class HTMLResource(HttpResource):
    #HTML无需特殊处理，直接返回网络返回的数据
    def parse(self, content):
        return super(HTMLResource, self).parse(content)


class JsonResource(HttpResource):
    #JSON资源解析成dict后再返回
    def parse(self, content):
        try:
            # try{window.Q.__callbacks__.cbhacjhl( {} )}catch(e){}
            if content.startswith('try{'):
                content = content[4:content.rfind('}catch(')]
            if not content.startswith('{'):
                if not content.startswith('['):
                    content = content[content.find('{'):].rstrip(';').rstrip(')')
            json_content = simplejson.loads(content)
            return json_content
        except Exception as e:
            if self.retry_count >= self.max_retry_count:
                if not 'no_none_content' in locals().keys():
                    pass
                    #self._print_log('no content')
                elif not 'json_content' in locals().keys():
                    pass
                    #self._print_log('error json data')
                else:
                    self._print_log('unexpected data')
                    logging.warning('exception: %s', e, exc_info=1)
            return None

class XmlResource(HttpResource):
    #Xml资源解析成dict后再返回
    def parse(self, content):
        try:
            # content = super(XmlResource, self).parse(content)
            xml_content = xmltodict.parse(content)
            return xml_content
        except Exception as e:
            if self.retry_count >= self.max_retry_count:
                if not 'no_none_content' in locals().keys():
                    pass
                    #self._print_log('no content')
                elif not 'json_content' in locals().keys():
                    pass
                    #self._print_log('error json data')
                else:
                    self._print_log('unexpected data')
                    logging.warning('exception: %s', e, exc_info=1)
            return None
