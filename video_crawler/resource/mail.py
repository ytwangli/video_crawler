# -*- coding: utf-8 -*-

import traceback
import smtplib
import email
from email.mime.text import MIMEText

class SendMail(object):
    def __init__(self):
        self.send_from = 'zurzer@126.com'
        self.username = 'zurzer'
        self.password = 'temexaofwgoykpnm'
        self.real_password = 'test123'
        # zhangqi_iqiyi@163.com

    def send_text_mails(self, title, content, send_addrs):
        try:
            send_to = ['zurzer@126.com']
            send_to.extend(send_addrs)
            msg = MIMEText(content, _subtype='html', _charset='utf8')
            msg['From'] = self.send_from
            msg['To'] = ','.join(send_to)
            msg['Subject'] = title
            #生成正文
            server = smtplib.SMTP()
            server.connect('smtp.126.com', 25)
            server.login(self.username, self.password)
            server.sendmail(self.send_from, send_to, msg.as_string())
            server.quit()
        except Exception as e:
            print e
            traceback.print_exc()

    def send_data_mails(self, title, name, data_read, send_addrs):
        try:
            send_to = ['zurzer@126.com']
            send_to.extend(send_addrs)  # , 'diwenhua@qiyi.com', 'maxchen@qiyi.com', 'tiansihua@qiyi.com'
            msg = email.MIMEMultipart.MIMEMultipart()
            text_msg = email.MIMEText.MIMEText(u"具体内容见附件", _subtype='html', _charset='utf8')
            msg.attach(text_msg)

            contype = 'text/csv'
            maintype, subtype = contype.split('/', 1)
            file_msg = email.MIMEBase.MIMEBase(maintype, subtype)
            file_msg.set_payload(data_read)
            email.Encoders.encode_base64(file_msg)
            file_msg.add_header('Content-Disposition', 'attachment', filename = name+'.csv')
            msg.attach(file_msg)

            msg['From'] = self.send_from
            msg['To'] = ','.join(send_to)
            msg['Subject'] = title
            msg['Date'] = email.Utils.formatdate( )

            server = smtplib.SMTP()
            server.connect('smtp.126.com', 25)
            server.login(self.username, self.password)
            server.sendmail(self.send_from, send_to, msg.as_string())
            server.quit()
        except Exception as e:
            print e
            traceback.print_exc()


