#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import os
import sys
import gzip

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    url = 'http://opensource.apple.com/source/mDNSResponder/mDNSResponder-624.1.2/'


    # data = {}
    # datanum = []
    # basenum = 0
    # count = 0
    # base_path = 'D:\\work\\video_data\\youku\\old\\'
    # handle = gzip.open(base_path+'tudou_'+str(basenum)+'.gz', 'w+')
    #
    # while(True):
    #     path = base_path+'youku_'+str(count)+'.csv'
    #     if os.path.exists(path):
    #         for line in open(path, 'r'):
    #             if line == '\n':
    #                 continue
    #             id_num = int(line[0: line.find(',')])
    #             tmps = line.split(',')
    #             data[id_num] = tmps[0]+','+tmps[1]+','+tmps[2]+','+tmps[7]
    #             datanum.append(id_num)
    #     datanum.sort()
    #     for id_num in datanum:
    #         print data[id_num]
    #     data.clear()
    #     count += 1
    #     if count >= 10000000:
    #         break
    # handle.close()