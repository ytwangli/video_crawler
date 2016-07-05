# -*- coding: utf-8 -*-
import sys
import datetime
import MySQLdb
import socket

class DataBase(object):
    # 主库(写)：mysql -uvideomonitor -pevPoLol4 -hsh.videomonitor.w.qiyi.db -P8597;
    # 备库(读)：mysql -uvideomonitor -pevPoLol4 -hsh.videomonitor.r.qiyi.db -P8597;
    # qidun:iqSklq2P
    @staticmethod
    def open_conn_qidun():
        conn = MySQLdb.connect(
            host='sh.videomonitor.w.qiyi.db',
            port=8597,
            user='qidun',
            passwd='iqSklq2P',
            db='qidun',
            charset='utf8',
        )
        cur = conn.cursor()
        return conn, cur

    @staticmethod
    def open_conn_video():
        conn = MySQLdb.connect(
            host='sh.videomonitor.w.qiyi.db',
            port=8597,
            user='videomonitor',
            passwd='evPoLol4',
            db='videomonitor',
            charset='utf8',
        )
        cur = conn.cursor()
        return conn, cur

    @staticmethod
    def open_conn_video_read():
        conn = MySQLdb.connect(
            host='sh.videomonitor.r.qiyi.db',
            port=8597,
            user='videomonitor',
            passwd='evPoLol4',
            db='videomonitor',
            charset='utf8',
        )
        cur = conn.cursor()
        return conn, cur

    @staticmethod
    def close_conn(conn, cur):
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def insert_proxyips(ip_list):
        conn, cur = DataBase.open_conn_qidun()
        cur.executemany('insert into proxyips(ip,port,protocol,location,proxy_type,speed,host,append,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', ip_list)
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_proxyips():
        ip_set = set()
        conn, cur = DataBase.open_conn_qidun()
        cur.execute('SELECT ip FROM proxyips')
        for data in cur.fetchall():
            ip_set.add(data[0])
        DataBase.close_conn(conn, cur)
        return ip_set

    @staticmethod
    def insert_baidu_tieba(data):
        conn, cur = DataBase.open_conn_qidun()
        exe_time = datetime.datetime.now()
        cur.execute('insert into baidu_tiebas(name,title,url,date_str,status,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s)', (data[0], data[1], data[2], data[3], 0, exe_time, exe_time))
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def insert_sina_weibo(data):
        conn, cur = DataBase.open_conn_qidun()
        exe_time = datetime.datetime.now()
        cur.execute('insert into sina_weibos(name,text,url,sub_url,status,created_at,updated_at) values(%s,%s,%s,%s,%s,%s,%s)', (data[0], data[1], data[2], data[3], 0, exe_time, exe_time))
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_sina_weibo_urls():
        sina_weibo_urls = set()
        sina_weibo_online_urls = []
        conn, cur = DataBase.open_conn_qidun()
        exe_time = datetime.datetime.now()
        cur.execute('SELECT url, status, id, created_at FROM sina_weibos')
        for data in cur.fetchall():
            status = int(data[1])
            if status == 0:
                sina_weibo_online_urls.append([data[0], str(data[2]), data[3]])
            sina_weibo_urls.add(data[0])
        conn.commit()
        DataBase.close_conn(conn, cur)
        return sina_weibo_urls, sina_weibo_online_urls

    @staticmethod
    def update_sina_weibo_urls(sina_weibo_offline_urls):
        conn, cur = DataBase.open_conn_qidun()
        for url, idstr in sina_weibo_offline_urls:
            cur.execute('UPDATE sina_weibos SET status=1 WHERE id='+idstr)
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def update_data(site, idstr, date_str, status='2'):
        conn, cur = DataBase.open_conn_video()
        cur.execute('UPDATE '+site+'_long SET date_str="'+date_str+'" , status='+status+' WHERE id='+idstr)
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def update_datas(site, datas):
        conn, cur = DataBase.open_conn_video()
        count = 0
        for data in datas:
            count += 1
            cur.execute('UPDATE '+site+'_long SET date_str="'+data[1]+'" , status='+data[2]+' WHERE id='+data[0])
            if count % 200 == 0:
                conn.commit()
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def update_keys(site, datas):
        conn, cur = DataBase.open_conn_video()
        for data in datas:
            cur.execute('UPDATE '+site+'_long SET date_str="'+data[1]+'" , status='+data[2]+' WHERE id='+data[0])
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_local_ip():
        ip_str = ''
        try:
            ip_str = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            print e
        return ip_str

    @staticmethod
    def insert_pathdata(site, image_base_path, date_str):
        conn, cur = DataBase.open_conn_video()
        dir_path = image_base_path+site+'/'+date_str
        exe_time = datetime.datetime.now()
        ip_str = DataBase.get_local_ip()
        cur.execute('insert into pathdata(host,site,row_type,image_dir,key_type,key_detail,key_path,code_flag,used_flag,new_flag,ip_str,date_str,create_date,update_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (2, site,1, dir_path,'','', '', 0, 1, 1, ip_str,date_str,exe_time,exe_time))
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_pathdatas(site):
        pathdata_list = []
        conn, cur = DataBase.open_conn_video()
        cur.execute('SELECT id,image_dir,key_path,date_str FROM pathdata WHERE site = "'+site+'" order by id asc;')
        for data in cur.fetchall():
            pathdata_list.append([data[0], data[1], data[2], data[3]])
        return pathdata_list

    @staticmethod
    def update_pathdatas(datas):
        conn, cur = DataBase.open_conn_video()
        for data in datas:
            cur.execute('UPDATE pathdata SET image_dir="'+data[1]+'", key_path="'+data[2]+'", date_str="'+data[3]+'" WHERE id='+str(data[0]))
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def del_pathdata(idstr):
        conn, cur = DataBase.open_conn_video()
        cur.execute('DELETE FROM pathdata WHERE id='+idstr)
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_iqiyidatas(site):
        pathdata_list = []
        conn, cur = DataBase.open_conn_video()
        cur.execute('SELECT id,image_dir,key_path,date_str FROM iqiyidata WHERE site = "'+site+'" order by id asc;')
        for data in cur.fetchall():
            pathdata_list.append([data[0], data[1], data[2], data[3]])
        return pathdata_list

    @staticmethod
    def update_iqiyidatas(datas):
        conn, cur = DataBase.open_conn_video()
        for data in datas:
            cur.execute('UPDATE iqiyidata SET image_dir="'+data[1]+'", key_path="'+data[2]+'", date_str="'+data[3]+'" WHERE id='+str(data[0]))
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def del_iqiyidata(idstr):
        conn, cur = DataBase.open_conn_video()
        cur.execute('DELETE FROM iqiyidata WHERE id='+idstr)
        conn.commit()
        DataBase.close_conn(conn, cur)

    @staticmethod
    def get_new_datas(site):
        data_list = []
        bad_data_list = []
        conn, cur = DataBase.open_conn_video()
        max_id = 9999999999
        cur.execute('SELECT max(id) FROM '+site+'_long WHERE status>0;')
        for data in cur.fetchall():
            max_id = data[0]
        cur.execute('SELECT id,sid,title,date_str FROM '+site+'_long WHERE status=0 and id>'+str(max_id)+' order by id asc;')
        for data in cur.fetchall():
            title = data[2]
            is_ok = True
            for bad_word in DataBase.get_bad_words():
                if bad_word in title:
                    is_ok = False
                    break
            if is_ok:
                data_list.append([data[0],data[1],data[3]])
            else:
                bad_data_list.append([data[0],data[1],data[3]])
        DataBase.close_conn(conn, cur)

        datas = []
        print len(bad_data_list)
        for bad_data in bad_data_list:
            datas.append([str(bad_data[0]), '', '-1'])
        DataBase.update_datas(site, datas)
        del datas[0: len(datas)]

        return data_list

    @staticmethod
    def get_datas(site, cond):
        data_list = []
        bad_data_list = []
        conn, cur = DataBase.open_conn_video()
        cur.execute('SELECT id,sid,title,date_str FROM '+site+'_long WHERE '+cond+' order by id asc;')
        for data in cur.fetchall():
            title = data[2]
            is_ok = True
            for bad_word in DataBase.get_bad_words():
                if bad_word in title:
                    is_ok = False
                    break
            if is_ok:
                data_list.append([data[0],data[1],data[3]])
            else:
                bad_data_list.append([data[0],data[1],data[3]])
        DataBase.close_conn(conn, cur)
        return data_list, bad_data_list

    @staticmethod
    def get_ciddatas(site, cond):
        data_list = []
        bad_data_list = []
        conn, cur = DataBase.open_conn_video()
        cur.execute('SELECT id,video_cid,title,date_str FROM '+site+'_long WHERE '+cond+' order by id asc;')
        for data in cur.fetchall():
            title = data[2]
            is_ok = True
            for bad_word in DataBase.get_bad_words():
                if bad_word in title:
                    is_ok = False
                    break
            if is_ok:
                data_list.append([data[0],data[1],data[3]])
            else:
                bad_data_list.append([data[0],data[1],data[3]])
        DataBase.close_conn(conn, cur)
        return data_list, bad_data_list

    @staticmethod
    def get_new_ciddatas(site):
        data_list = []
        bad_data_list = []
        conn, cur = DataBase.open_conn_video()
        max_id = 9999999999
        cur.execute('SELECT max(id) FROM '+site+'_long WHERE status>0;')
        for data in cur.fetchall():
            max_id = data[0]
        cur.execute('SELECT id,video_cid,title,date_str FROM '+site+'_long WHERE status=0 and id>'+str(max_id)+' order by id asc;')
        for data in cur.fetchall():
            title = data[2]
            is_ok = True
            for bad_word in DataBase.get_bad_words():
                if bad_word in title:
                    is_ok = False
                    break
            if is_ok:
                data_list.append([data[0],data[1],data[3]])
            else:
                bad_data_list.append([data[0],data[1],data[3]])
        DataBase.close_conn(conn, cur)

        datas = []
        print len(bad_data_list)
        for bad_data in bad_data_list:
            datas.append([str(bad_data[0]), '', '-1'])
        DataBase.update_datas(site, datas)
        del datas[0: len(datas)]

        return data_list

    @staticmethod
    def get_bad_words():
        bad_words = [
            ' vs ', ' VS ', '白银', '原油', '现货', '理财', 'cad', '3dmax', '佛', '教程', '讲座', '减肥', '淘宝', '国学',
            '课程', '股票', '英语', '物理', '高中', '初中', '年级', 'DOTA', 'LOL', '法师', '数学', '小学', '钢筋', '华严',
            '解说', '瑜伽', '高考', '中考', '攻略', '施工', '期货', '项目', '黄帝内经', '炉石传说', '工程', '弱电', '装修',
            '工厂', '混凝土', '主讲', '中学', '考试', '大学', '演义', '哑铃操', '郑多燕', '医师', '创业', '篮球', '法師',
            '足球', '机电', '相声', '广场舞', '见面会', 'LOGO', 'logo', 'MP3', 'mp3', '真三国', '仙剑', '怪物猎人',
            '最终幻想', '星际', '实况', '通关', '轩辕剑', '游戏', '古剑奇谭', '单机', '电玩', '剧情', '介绍', '简介',
            '产品', '宝宝', '国服', '人物', '讲坛', '资料', '新闻', '小智碧哥', '演员', '基督', '圣经', '投资', '戏曲',
            '楞严', '福音', '得分', '温网', '男单', '男双', '女单', '女双', '双打', '公开赛', '教学', '植物大战', '机器人',
            '教育', '因果', '老师', '速成', '股市', '小说', '无聊是光', '星竞界', '英雄时刻', '决赛', '小组赛', 'MVP',
            'mvp', '祖安', '电1', '预选赛', '联赛', '皮城警备', '开视频', '刀塔', 'EXCEL', 'excel', 'ppt', '实战',
            '锦标赛', 'wmv', '专辑', '歌曲', '主题曲', '刘德华', 'EXO', 'exo', '周润发', '周星驰', '成龙', '李连杰',
            '僵尸', '林正英', '古天乐', '甄子丹', '梁朝伟', '海报', 'PS', 'ps', '基础', '婚纱', '照片', 'wav', 'WAV',
            '拳皇', '魔兽', '发布', '彩蛋', '见面', '使命召唤', 'lol', '首映礼', '宣传片', '片尾曲', '图片', '素材',
            '网页', '广播', '聊天', '暴走', '砂浆', '婚礼', '煤矿', '流程', '安全', '脚手架', '电梯', '入门', '门窗',
            '炒股', '风水', '钢', '京剧', '土方', '排水', '措施', '马里奥', '网店', '钢结构', '钢丝', '复试', '面试',
            '工艺', '红色警戒', '网站', '3DMAX', '单片机', 'HOME键', '巫师', '办公', 'office', '设计', '建筑', '服装',
            '演唱', '川剧', '粤剧', '越剧', '温州鼓词', '技术', '黄金', '操盘', '哈工大', '解盘', '趋势', '清华', '演讲',
            '运动会', '亲子', '辅导', '曾仕强', '幼儿园', '汇演', '优质课', '六一', '科学', '领导', '公务员', '申论',
            '国考', '公考', '培训', '尚学堂', '营销', '太极拳', '弘法', '开示', '宣化上人', '南宁小胖', '演讲', '海云继梦',
            '大纲', '考研', '海文', '会计', '刑法', '民法', '西医', '中医', '经济法', '政治', '人教', '心理学', '咨询',
            '推广', '微信', '支付', '上海交大', '西安交大', '第九资源', '晚会', '物业', '语文', '化学', '生物', '哲学',
            '高一', '高二', '高三', '初一', '初二', '初三', '新年', '联欢', '思想', '毛泽东', '报告', '研究', '本科',
            '药师', '博士', '护师', '执业', '阅兵', '菩萨', '地产', '梦幻西游', '体育', '直播', '录像', '豫剧', '51CTO学院',
            '郎咸平', '净土', '淨土', '无量寿经', '無量壽經', '圓覺', '圆觉', '金剛經', '書經', '維摩', '居士', '比丘',
            '護國經', '放生', '阿彌陀', '華嚴', '壇經', '易經', '阿弥托', '华严', '坛经', '易经', '书经', '金刚经',
            '陈安之', '马云', '潘小夏', '直销', '股一道长', '案例', '真题', '押题', 'Word', '课件', '建造师', '屋面',
            '防水', '名师', '质检', '土建', '实务', '造价', '市政', '安装', '新股', '芭蕾', '大盘', '个股', '王兴华',
            '热舞', '夜店', '酒吧', '紫禁皇朝', '指标', '音乐', '巡演', 'OFFICE', 'Office', 'jquery', 'jQuery', '外汇'
            'java', 'Java', 'JAVA', '尚硅谷', 'HTML', 'html', 'JavaScript', '表单', 'C语言', 'python', '杨建明',
            'iPhone', 'word', 'Android', 'PHP', 'php', 'SQL', 'sql', '数据', '质量', '短线', '数据', '早盘', '实盘'
            '健身', '三国杀', '黑马', 'K线', '行情', '散户', '集训', '大赛', '教师', '法学', '管理学', '益学堂', '生理学',
            '法律', '法理', '唱歌', '发声', '硕士', '经络', '力学', '针灸', 'Q348948909', '学习班', '冲刺', '烹饪', '新东方',
            '法语', '西语', '西班牙语', '葡萄牙语', '德语', '小智', '韩服', '战旗全明星', '精英赛', '亚索', '人头', '建模',
            'maya', '家居', '家具', '渲染', '建材', '冠军', '庐剧', '曲剧', '锡剧', '潮剧', '衢州', '晋剧', '二人转',
            '婺剧', '蒲剧', '黄梅戏', '楚剧', '庐剧', 'CAD', '软件', '测算', '计算', '算法', '方案', '预算', '审计',
            '早读', '电工', '考点', '备考', '模考', '考核', '程序', '管理', '余世维', '调节', '做法', '营养师', '人力资源',
            '招聘', '启示录', '内科', '外科', '等奖', '白板', '制剂', '药物', '临床', '函数', 'Excel', '职场', '金正昆',
            '商务', '挖矿', '群书', '開示', '法会', '祭祖', '系念',
            '中超', '德甲', '女排', '围棋', '评测', '学车', '乒超', '天天酷跑', '三国争霸'
        ]
        return bad_words
