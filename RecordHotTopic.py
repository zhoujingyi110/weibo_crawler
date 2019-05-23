from SpliderHotTopic import SpliderHotTopic

if __name__ == '__main__':

    record = SpliderHotTopic()
    # 获取热门话题排行榜信息 没个小时抓取一次
    record.record_hot_topic()
    record.close()