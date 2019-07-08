#1 /usr/bin/env python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import json
import pandas as pd
import datetime
import time
import sys
import os

from twitter_manager import TwitterClient

class KULASISGateway():

    def __init__(self):

        #ECS-IDを読み込む
        ecs_account = {"ecs-id":os.environ["ECSID"],"password":os.environ["PASSWORD"]}

        #ヘッドレスブラウザを起動
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,1024')
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=options)

        #ログイン処理
        login_url = "https://www.k.kyoto-u.ac.jp/student/la/top"
        self.driver.get(login_url)
        self.driver.find_element_by_id("username").send_keys(ecs_account["ecs-id"])
        self.driver.find_element_by_id("password").send_keys(ecs_account["password"])
        self.driver.find_element_by_name("_eventId_proceed").click()

    #全学共通科目と専門科目の休講情報をまとめたDataFrameを作成
    # df["time"] : 何時間目
    # df["subject"] : 教科名
    # df["teacher"] :担当教員
    # df["date"] : 休講日時
    def createInfoDF(self):

        first_liberal_url = "https://www.k.kyoto-u.ac.jp/student/la"
        first_special_url = "https://www.k.kyoto-u.ac.jp/student/u/"
        specials = ["let","ed","l","ec","s","med","medh","p","t","a","h"]
        last_url = "/notice/cancel"

        #DataFrameを初期化
        df = pd.DataFrame()
        df_liberal = pd.DataFrame()
        df_special = pd.DataFrame()

        #全学共通科目のDataFrameを作成
        df_liberal = self.fetchInfoTable(first_liberal_url+last_url)

        #専門科目のDataFrameを作成
        for special in specials:
            tmp_df = self.fetchInfoTable(first_special_url+special+last_url)
            df_special = pd.concat([df_special,tmp_df])

        #ブラウザを閉じる
        self.driver.close()
        self.driver.quit()

        #データの整理
        df_liberal = df_liberal.iloc[:,0:4]
        df_liberal.columns =["time","subject","teacher","date"]

        df_special = df_special.iloc[:,0:5]
        df_special.columns =["time","subject","teacher","department","date"]

        #一つのDataFrameにまとめる
        df = pd.concat([df_liberal,df_special[["time","subject","teacher","date"]]])
        df = df[df["time"] != "集中"]
        #データの整形
        change_time = lambda x: x[-2:-1]
        delete_time = lambda x : x[:-4]
        df["time"] = df["date"].apply(change_time)
        df["time"] = df["time"].astype(int)
        df["date"] = df["date"].apply(delete_time)
        df["date"] = pd.to_datetime(df["date"])
        df["date"] = df["date"].dt.date
        df["teacher"] = df["teacher"].str.replace("\n"," ")

        return df

    #urlにあるテーブルデータを読み込みDataFrameで返す
    def fetchInfoTable(self,url):
        df = pd.DataFrame()
        self.driver.get(url)

        #テーブルデータを取得
        for class_name in ["odd_normal","even_normal"]:
            elements = self.driver.find_elements_by_class_name(class_name)

            for e in elements:
                tds = e.find_elements_by_tag_name("td")
                data = []
                for td in tds:
                    data.append(str(td.text))
                tmp_df = pd.DataFrame(data)
                df = df.append(tmp_df.T)

        return df

    #canceled_date日のbegin限~5限目の休講情報のツイート文章をリストで返す
    def createTweetMessages(self,df,canceled_date,begin):
        msgs = []
        data = []
        now_time = datetime.datetime.now().strftime("%H:%M")
        canceled_date_str = canceled_date.strftime("%m/%d")

        msg =  canceled_date_str +"の休講情報[{}]".format(now_time)

        for i in range(begin,6):
            #i限目のDataFrameを作成
            tmp_df = df[df["time"] == i]

            #dataに休講情報文を1行づつ格納する
            data = []
            for index, row in tmp_df.iterrows():
                data.append("{}({})\n".format(row["subject"],row["teacher"]))


            #140字に入るだけのツイート分を作成しmsgsに格納する
            for j in range(len(data)):
                if (j == 0 and len(msg) + len(data[j]) + len("\n【n限】\n")  < 140) or (j != 0 and len(msg) + len(data[j]) < 140):
                    if j == 0:
                        msg +="\n【{}限】\n".format(i)
                    msg += data[j]
                else:
                    msgs.append(msg)
                    msg = canceled_date_str +"の休講情報[{}]".format(now_time)
                    msg += "\n【{}限】\n".format(i) if j == 0 else "\n【{0}限続き】\n".format(i)
                    msg += data[j]

        msgs.append(msg)
        return msgs

def main():
    begin = sys.argv[1]     #1~5の場合その時限からの情報をpostする。6の場合は明日の休講情報をすべてpostする

    #インスタンス作成
    kulasis_cli = KULASISGateway()

    #休講情報を取得
    df = kulasis_cli.createInfoDF()

    today = datetime.date.today()

    if int(begin) == 6:
        tomorrow = today + datetime.timedelta(days = +1)
        use_df = df[df["date"] == tomorrow ]
        msgs = kulasis_cli.createTweetMessages(use_df,tomorrow,1)
    else:
        use_df  = df[df["date"] == today ]
        msgs = kulasis_cli.createTweetMessages(use_df,today,int(begin))

    #ツイッタークライアントを作成
    twitter_cli = TwitterClient()

    for msg in msgs:
        twitter_cli.post(msg)

if __name__ == "__main__":
    main()
