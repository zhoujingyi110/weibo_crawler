# -*- coding: utf-8 -*-
import requests
import time
import re
import urllib
import datetime
from openpyxl import Workbook
import db_connect

class SpliderHotTopic(object):

    def __init__(self):
        self.topic_page = 1
        self.weibo_page = 100
        self.batch_no = datetime.datetime.now().strftime("%Y%m%d%H")
        self.topic_id = int(datetime.datetime.now().strftime("%m%d%H%M"))*1000
        self.weibo_id = int(datetime.datetime.now().strftime("%Y%m%d%H"))*100000

        self.topic_list = []
        self.topic_info = []
        self.topic_weibo = {}

        self.db = db_connect.DB()
        delete_sql = "delete from hot_topic"
        delete_sql1 = "delete from hot_wb"

        # self.db.execute_sql(delete_sql)
        # self.db.execute_sql(delete_sql1)

        self.url = "https://m.weibo.cn/api/container/getIndex?containerid=231648_-_1_-_all_-_%E8%AF%9D%E9%A2%98%E6%A6%9C_-_1&luicode=10000011&lfid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Dtopicband&page={}"
        self.weibo_url = "https://m.weibo.cn/api/container/getIndex?containerid=231522type%3D1%26t%3D10%26q%3D{}&extparam=c_type%3D81%26pos%3D1-0-4&luicode=10000011&lfid=231648_-_1_-_all_-_%E8%AF%9D%E9%A2%98%E6%A6%9C_-_1&page={}"

        self.header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36",
                    'Referer': 'https://m.weibo.cn/',
                    'Host': 'm.weibo.cn',
                    # 'Cookie': '_T_WM=48296289948; WEIBOCN_WM=3349; SCF=AuZ-Kers5-Jk64vm2JgTg7w8GgBPRPIZqTChMNxX8JvrKGGdXHRw_fCpwoVWwjxpJvmDkqKXRdBybNq0Ouhokis.; SUB=_2A25xyuElDeRhGeBN6FoQ9i3EyzmIHXVTNI9trDV6PUJbktBeLVStkW1NRGB1HkIPIy9ADOLwQI0fwA2EHNBbO7N-; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFxYVIgUXT_e4ivU1N6WWWQ5JpX5KzhUgL.Foq0e0npSoeReh-2dJLoI0YLxK-LBKML12zLxKMLB.zL1hnLxK-LBKqL1hzLxKBLBonL1h5LxKML1-2L1hBLxK-L1hqLBoMLxKqLB.eLBK5t; SUHB=0h1JyaAW7oA8ye; SSOLoginState=1557041526; WEIBOCN_FROM=1110006030; MLOGIN=1; XSRF-TOKEN=3b87e4; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D106003type%253D25%2526t%253D3%2526disable_hot%253D1%2526filter_type%253Dtopicband%26fid%3D231648_-_1_-_all_-_%25E8%25AF%259D%25E9%25A2%2598%25E6%25A6%259C_-_1%26uicode%3D10000011'
                    }

    #获取热门话题榜
    def get_hot_topic(self):
        session = requests.session()
        record = True
        for i in range(self.topic_page):
            if record:
                print("\n*****正在获取第{}页*****".format(i + 1))
                the_url = self.url.format(i+1)
                try:
                    r = session.get(the_url, headers=self.header)
                    res = r.json()
                    if res['ok']==0:
                        record = False
                    else:
                        self.get_topic_list(res)
                except requests.exceptions.ConnectionError:
                    print("！！！网络连接出错，请检查网络！！！")

                time.sleep(2)
            else:
                break

    #解析返回页面，得到topic_list
    def get_topic_list(self,res):

        #将阅读数和讨论数转化成int类型
        def dealnum(num):
            if "万" in num:
                num = float(num.replace("万", ""))*10000
            elif "亿" in num:
                num = float(num.replace("亿", ""))*100000000
            else:
                return int(num)
            return int(num)

        #抓取热门话题
        for cards in res.get("data").get("cards"):
            if cards.get("card_group") is None:
                continue
            for card in cards.get("card_group"):
                title = card.get("title_sub")
                topmark = card.get("top_mark_text")
                desc1 = card.get("desc1")
                desc2 = card.get("desc2").split(" ")
                discuss = desc2[0]
                read = desc2[1]
                scheme = card.get("scheme")
                self.topic_id = self.topic_id + 1
                discuss = dealnum(discuss.replace("讨论", ""))
                read = dealnum(read.replace("阅读", ""))
                top = [str(self.topic_id), self.batch_no,str(topmark), title, desc1,str(discuss), str(read),scheme]
                self.topic_info.append(top)
                self.topic_list.append(title)
                print(top)

    #抓取热门话题下的微博，输入热门微博的title
    def get_topic_wb(self,title):
        #统一时间格式为：Y-M-D H:M:S
        def deal_time(created_time):
            current_time = datetime.datetime.now()
            if '刚刚' in created_time:
                return  current_time.strftime("%Y-%m-%d %H:%M:%S")
            if '分钟前' in created_time:
                created = current_time - datetime.timedelta(minutes=int(created_time.replace("分钟前","")))
                return created.strftime("%Y-%m-%d %H:%M:%S")
            if '小时前' in created_time:
                created = current_time - datetime.timedelta(hours=int(created_time.replace("小时前","")))
                return created.strftime("%Y-%m-%d %H:%M:%S")
            if '昨天' in created_time:
                created = current_time - datetime.timedelta(days=1)
                created = created.strftime("%Y-%m-%d") + " " + created_time.replace("昨天 ","")
                created = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M")
            else:
                time_list = created_time.split("-")
                if len(time_list) == 2:
                    created = current_time.strftime("%Y") + "-" +created_time
                else:
                    created = created_time
                created = datetime.datetime.strptime(created, "%Y-%m-%d")
            return created.strftime("%Y-%m-%d %H:%M:%S")

        #获取微博
        text_bolg = []
        text_num = 0
        session = requests.session()
        blog_list = []
        created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i in range(self.weibo_page):
            time.sleep(2)
            # print("{}话题正在获取第{}页".format(title,i + 1))
            r = session.get(self.weibo_url.format(urllib.parse.quote(title), i + 1), headers=self.header)
            if r.content:
                try:
                    res = r.json()
                except:
                    continue

                # print(res)
                if res.get("ok") == 1:
                    for cards in res.get("data").get("cards"):
                        if cards.get("card_group") is None:
                            continue
                        for c in cards.get("card_group"):
                            if c.get("card_type") == 9:
                                mblog = c.get("mblog")
                                created_at = deal_time(mblog.get("created_at"))
                                text = mblog.get("text")
                                text = re.sub("<.*?>", "", text)
                                text = text.replace("'", "")
                                user = mblog.get("user")
                                user_id = user.get("id")
                                user_name = user.get("screen_name")
                                user_gender = user.get("gender")
                                user_verified = user.get("verified")
                                user_followers = user.get("followers_count")
                                user_follow = user.get("follow_count")
                                reposts = mblog.get("reposts_count")
                                coments = mblog.get("comments_count")
                                attitudes = mblog.get("attitudes_count")
                                self.weibo_id = self.weibo_id + 1

                                topic_blog = [str(self.weibo_id), self.batch_no, title, created_at, text, str(user_id), user_name, user_gender,
                                              str(user_verified), str(user_followers), str(user_follow), str(reposts), str(coments), str(attitudes)]
                                # print(mblog.get("created_at"))
                                # print(topic_blog)
                                if text not in text_bolg:
                                    text_bolg.append(text)
                                    blog_list.append(topic_blog)
                                    created = created_at
                                else:
                                    text_num += 1
                                    # print("重复")
                                    # print(text)
                else:
                    print("ok=0")

                    break
            else:
                print(r)
                continue
            if datetime.datetime.strptime(created, "%Y-%m-%d %H:%M:%S") < datetime.datetime.now() - datetime.timedelta(days=10):
                self.topic_weibo[title] = blog_list
                print("到了截止时间")
                break
        print("{}话题获取完毕".format(title))
        print(text_num)
        self.topic_weibo[title] = blog_list

    def save(self, filename, titlename, datas):
        wb = Workbook()
        bs = wb.active
        bs.append(titlename)
        for data in datas:
            bs.append(data)
        wb.save(filename)

    def save2db(self,table,datas):
        for data in datas:
            insert_sql =  "insert into {} values ('{}');".format(table,"','".join(data))
            self.db.execute_sql(insert_sql)

    def close(self):
        self.db.disconnect()

    def record_hot_topic(self):
        # 获取热门话题排行榜信息
        self.get_hot_topic()
        self.save2db("hot_topic", self.topic_info)

    def main(self):
        #获取热门话题排行榜信息
        self.get_hot_topic()
        # self.save2db("hot_topic", self.topic_info)
        # self.save("data/{}hot_topic.xlsx".format(datetime.datetime.now().strftime("%m%d%H%M")), ["topic_id", "batch_no","topmark", "title", "desc1","discuss", "read", "scheme"], self.topic_info)

        # path = "data/{}".format(datetime.datetime.now().strftime("%Y%m%d"))
        # if not os.path.exists(path):
        #     os.makedirs(path)
        #获取热门话题下微博信息
        for index in range(0,len(self.topic_list)):
            if index >= 0:
                title = self.topic_list[index]
                self.get_topic_wb(title)
                print(len(self.topic_weibo[title]))

                # print(self.topic_weibo[title])
                # print(self.topic_weibo[title].sort(key=self.topic_weibo[title].index))

                # self.save2db("hot_wb", self.topic_weibo[title])

                # self.save("data/{}/{}.xlsx".format(datetime.datetime.now().strftime("%Y%m%d"),title), ["weibo_id", "batch_no","title" ,"created_at", "text", "user_id", "user_name", "user_gender", "user_verified", "user_followers", "user_follow", "reposts", "coments", "attitudes"],
                          # self.topic_weibo[title])


if __name__ == '__main__':
    test = SpliderHotTopic()
    test.main()
    test.close()
