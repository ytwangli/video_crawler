# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
import os
import datetime
import subprocess
from resource.database import DataBase

class Util(object):

    @staticmethod
    def movie_split_image(filepath, jpgdir, idstr):
        returncode = -1
        # ffmpeg -i 348857801.mp4 -vf fps=15 -qscale 2 -f image2 -c:v mjpeg 348857801/348857801%d.jpg
        # ffmpeg -i /mediaideo/iqiyi504p/373009300/1.f4v -vf fps=12.5 -qscale 2 -f image2 -c:v mjpeg 1_%d.jpg
        if not os.path.exists(jpgdir):
            os.makedirs(jpgdir)
        # 5s per image
        cmd_line = 'cd '+jpgdir+' && ffmpeg -i '+filepath+' -vf fps=0.2 -qscale 2 -f image2 -c:v mjpeg -ss 0 -t 120 '+idstr+'_%d.jpg'
        p = subprocess.Popen(cmd_line, shell=True)
        returncode = p.wait()
        return returncode

    @staticmethod
    def delete_empty_dir(datedir):
        if os.path.exists(datedir):
            dirnames = os.listdir(datedir)
            count = len(dirnames)
            for dirname in dirnames:
                jpgdir = os.path.join(datedir, dirname)
                if len(os.listdir(jpgdir)) == 0:
                    count -= 1
                    os.rmdir(jpgdir)
            if count == 0:
                print('remove empty dir: ' + datedir)
                os.rmdir(datedir)

    @staticmethod
    def get_path_datas(jpgbasedir):
        result1 = {}
        result2 = {}
        datedirnames = os.listdir(jpgbasedir)
        datedirnames.sort()
        for datedirname in datedirnames:
            datedir = os.path.join(jpgbasedir, datedirname)
            jpgdirnames = os.listdir(datedir)
            if len(jpgdirnames) == 0:
                print('remove empty dir: ' + datedir)
                os.rmdir(datedir)
                continue
            for jpgdirname in jpgdirnames:
                jpgdir = os.path.join(datedir, jpgdirname)
                # jpgnames = os.listdir(jpgdir)
                jpg_path2 = os.path.join(jpgdir, jpgdirname + '_20.jpg')
                jpg_path1 = os.path.join(jpgdir, jpgdirname + '_5.jpg')
                _id = int(jpgdirname)
                if os.path.exists(jpg_path2):
                    if _id in result2:
                        result2[_id].append(datedirname)
                    else:
                        result2[_id] = [datedirname]
                elif os.path.exists(jpg_path1):
                    if _id in result1:
                        result1[_id].append(datedirname)
                    else:
                        result1[_id] = [datedirname]
                else:
                    print('remove < 5 jpg dir: ' + jpgdir)
                    for filename in os.listdir(jpgdir):
                        os.remove(os.path.join(jpgdir, filename))
                    os.removedirs(jpgdir)
        return datedirnames, result1, result2

    @staticmethod
    def clean_datas(site, image_base_path):
        base_path = os.path.join(image_base_path, site)
        datedirnames, result1, result2 = Util.get_path_datas(base_path)
        datas1 = []
        datas, bad_datas = DataBase.get_datas(site, 'status>0')

        count = 0
        for _id, sid, date_str in bad_datas:
            print _id
            dirnames2 = result2.pop(_id, [])
            dirnames1 = result1.pop(_id, [])
            id_str = str(_id)
            for dirname in dirnames2:
                path1 = os.path.join(base_path, dirname, id_str)
                print('remove bad jpg dir: ' + path1)
                for filename in os.listdir(path1):
                    os.remove(os.path.join(path1, filename))
                os.removedirs(path1)
                continue
            for dirname in dirnames1:
                path1 = os.path.join(base_path, dirname, id_str)
                print('remove bad jpg dir: ' + path1)
                for filename in os.listdir(path1):
                    os.remove(os.path.join(path1, filename))
                os.removedirs(path1)
                continue
            count += 1
            datas1.append([id_str, '', '-1'])
            if count % 1000 == 0:
                DataBase.update_datas(site, datas1)
                del datas1[0: len(datas1)]
        DataBase.update_datas(site, datas1)
        del datas1[0: len(datas1)]

        count = 0
        for _id, sid, date_str in datas:
            print _id
            is_ok = False
            status = '0'
            date_str1 = ''
            dirnames2 = result2.pop(_id, [])
            dirnames1 = result1.pop(_id, [])
            id_str = str(_id)
            for dirname in dirnames2:
                if is_ok:
                    path1 = os.path.join(base_path, dirname, id_str)
                    print('remove repeat jpg dir: ' + path1)
                    for filename in os.listdir(path1):
                        os.remove(os.path.join(path1, filename))
                    os.removedirs(path1)
                    continue
                is_ok = True
                status = '2'
                date_str1 = dirname
            for dirname in dirnames1:
                if is_ok:
                    path1 = os.path.join(base_path, dirname, id_str)
                    print('remove repeat jpg dir: ' + path1)
                    for filename in os.listdir(path1):
                        os.remove(os.path.join(path1, filename))
                    os.removedirs(path1)
                    continue
                is_ok = True
                status = '1'
                date_str1 = dirname
            count += 1
            datas1.append([id_str, date_str1, status])
            if count % 1000 == 0:
                DataBase.update_datas(site, datas1)
                del datas1[0: len(datas1)]
        DataBase.update_datas(site, datas1)
        del datas1[0: len(datas1)]

        for _idx in result2.keys():
            dirnames2 = result2.pop(_idx, [])
            id_str = str(_idx)
            for dirname in dirnames2:
                path1 = os.path.join(base_path, dirname, id_str)
                print('remove not need jpg dir: ' + path1)
                for filename in os.listdir(path1):
                    os.remove(os.path.join(path1, filename))
                os.removedirs(path1)
                continue

        for _idx in result1.keys():
            dirnames1 = result1.pop(_idx, [])
            id_str = str(_idx)
            for dirname in dirnames1:
                path1 = os.path.join(base_path, dirname, id_str)
                print('remove not need jpg dir: ' + path1)
                for filename in os.listdir(path1):
                    os.remove(os.path.join(path1, filename))
                os.removedirs(path1)
                continue

    @staticmethod
    def clean_baddatas(site, image_base_path):
        datas, bad_datas = DataBase.get_datas(site, 'date_str LIKE "%201%"')
        count = len(bad_datas)
        datas = []
        for data in bad_datas:
            _id, sid, datedirname = data
            id_str = str(_id)
            jpgdir = os.path.join(image_base_path, site, datedirname, id_str)
            print('remove bad jpg dir: ' + jpgdir)
            for filename in os.listdir(jpgdir):
                os.remove(os.path.join(jpgdir, filename))
            os.removedirs(jpgdir)
            count -= 1
            datas.append([id_str, '', '-1'])
            if count % 1000 == 0:
                DataBase.update_datas(site, datas)
                del datas[0: len(datas)]

    @staticmethod
    def clean_keys(site, image_base_path, oldname, newname):
        base_path = os.path.join(image_base_path, site)
        datedirnames = {}
        for datedirname in os.listdir(base_path):
            datedirnames[datedirname] = 0
        # id,image_dir,key_path,date_str
        pathdata_list = DataBase.get_pathdatas(site)
        datas = []
        for data in pathdata_list:
            key_path = data[2]
            date_str = data[3]
            data[1] = data[1].replace(oldname, newname)
            data[2] = data[2].replace(oldname, newname)
            if date_str in datedirnames:
                if datedirnames[date_str] == 0:
                    datedirnames[date_str] = 1
                    datas.append(data)
                    # new_key_path = data[2].replace('youku', 'youk1')
                    new_key_path = data[2]
                    if key_path != '' and not os.path.exists(new_key_path):
                        jpgdirnames = os.listdir(os.path.join(base_path, date_str))
                        handle = open(new_key_path, 'w+')
                        for line in open(key_path, 'r'):
                            if len(line) > 10:
                                # /media/image/sohu/20150603/2402960/2402960_18.jpg
                                jpgdirname = line[line.rfind('/')+1: line.rfind('_')]
                                if jpgdirname in jpgdirnames:
                                    line = line.replace(oldname, newname)
                                    handle.write(line)
                        handle.close()
                else:
                    print 'del repeat key path data:' + date_str
                    DataBase.del_pathdata(str(data[0]))
            else:
                print 'del not exist key path data:' + date_str
                DataBase.del_pathdata(str(data[0]))
        for datedirname in datedirnames.keys():
            if datedirnames[datedirname] == 0:
                print 'insert key path data:' + datedirname
                DataBase.insert_pathdata(site, image_base_path, datedirname)
        DataBase.update_pathdatas(datas)

    @staticmethod
    def clean_iqiyi_keys():
        site = 'iqiyi'
        image_base_path = '/media/0mage'
        base_path = os.path.join(image_base_path, site)
        jpgdirnames = {}
        for jpgdirname in os.listdir(base_path):
            jpgdirnames[jpgdirname] = 0
        # id,image_dir,key_path,date_str
        iqiyidata_list = DataBase.get_iqiyidatas(site)
        datas = []
        for data in iqiyidata_list:
            image_dir = data[1]
            key_path = data[2].replace('iqiyi_all', 'iqiyi')
            tvid = image_dir[image_dir.rfind('/')+1:]
            data[1] = data[1].replace('iqiyi_all', 'iqiyi').replace('/media/image/', '/media/0mage/')
            data[2] = data[2].replace('iqiyi_all', 'iqiyi').replace('/media/image/', '/media/0mage/')
            data[3] = tvid
            if jpgdirname in jpgdirnames:
                if jpgdirnames[tvid] == 0:
                    jpgdirnames[tvid] = 1
                    datas.append(data)
                    new_key_path = data[2]
                    if key_path != '' and not os.path.exists(new_key_path):
                        handle = open(new_key_path, 'w+')
                        for line in open(key_path, 'r'):
                            if len(line) > 10:
                                line = line.replace('iqiyi_all', 'iqiyi').replace('/media/image/', '/media/0mage/')
                                handle.write(line)
                        handle.close()
                else:
                    print 'del repeat key path data:' + tvid
                    DataBase.del_iqiyidata(str(data[0]))
            else:
                print 'del not exist key path data:' + tvid
                DataBase.del_iqiyidata(str(data[0]))
        for jpgdirname in jpgdirnames.keys():
            if jpgdirnames[jpgdirname] == 0:
                print 'insert key path data:' + jpgdirname
                # DataBase.insert_iqiyidata(site, image_base_path, datedirname)
        DataBase.update_iqiyidatas(datas)

    @staticmethod
    def clean_datedirs(site, image_base_path, dirname, end_date):
        path = os.path.join(image_base_path, site, dirname)
        jpgdirnames = os.listdir(path)
        jpgdirnames.sort()
        oneday = datetime.timedelta(days=1)
        count = len(jpgdirnames)
        i = 0
        date_str = end_date.strftime('%Y%m%d')
        path1 = os.path.join(image_base_path, site, date_str)
        print path1
        os.mkdir(path1)
        while count > 0:
            count -= 1
            i += 1
            name = jpgdirnames[count]
            src_path = os.path.join(path, name)
            dst_path = os.path.join(path1, name)
            os.renames(src_path, dst_path)
            if i >= 1000:
                i = 0
                DataBase.insert_pathdata(site, image_base_path, date_str)
                end_date = end_date - oneday
                date_str = end_date.strftime('%Y%m%d')
                path1 = os.path.join(image_base_path, site, date_str)
                print path1
                os.mkdir(path1)
        if i > 0:
            DataBase.insert_pathdata(site, image_base_path, date_str)

    @staticmethod
    def WatermarkingDetect(video_path):
        # cmd_line = './VWMDetect '+video_path
        cmd_line = '/home/monitor/works/bin/VWMDetect '+video_path
        if os.path.exists(video_path):
            p = os.popen(cmd_line, 'r')
            content = p.read()
            # print content
            if 'iqiyi' in content:
                # print 'this is iqiyi video'
                return True
        return False

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    Util.clean_iqiyi_keys()
    # site = 'youku'
    # print site
    # image_base_path = "/media/image/"
    # Util.clean_keys(site, image_base_path, '/media/image/', '/media/image/')
    # Util.clean_datas(site, base_path)
    # Util.clean_datedirs(site, image_base_path, 'tmp1', datetime.date(2015,10,7))

    # Util.clean_keys(site, base_path, '/media/image/', '/media/2mage/')
    # site = 'youku'
    # print site
    # base_path = "/media/image/"+site
    # Util.clean_keys(site, base_path, '/media/image/', '/media/image/')