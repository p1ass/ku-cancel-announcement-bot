from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import pandas as pd
import datetime
import time
from requests_oauthlib import OAuth1Session
import sys
import os

#ヘッドレスブラウザを起動
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1280,1024')
driver = webdriver.Chrome(chrome_options=options)

#全学共通科目と専門科目の休講情報をまとめたDataFrameを作成
def createInfoDF():

    #ECS-IDを読み込む
    if os.name == "nt":
        f = open("./account.json","r")
    else:
        f = open("/home/ec2-user/KUCancelAnnouncementBot/account.json","r")
    account = json.load(f)
    f.close()


    first_liberal_url = "https://www.k.kyoto-u.ac.jp/student/la"
    first_special_url = "https://www.k.kyoto-u.ac.jp/student/u/"
    specials = ["let","ed","l","ec","s","med","medh","p","t","a","h",]
    last_url = "/notice/cancel"

    #まず全共のページに行く際にログイン処理をする
    driver.get(liberal_url+last_url)
    driver.find_element_by_id("username").send_keys(account["ecs-id"])
    driver.find_element_by_id("password").send_keys(account["password"])
    driver.find_element_by_name("_eventId_proceed").click()


    #DataFrameを初期化
    df = pd.DataFrame()
    df_liberal = pd.DataFrame()
    df_special = pd.DataFrame()

    #全学共通科目のDataFrameを作成
    df_liberal = fetchInfoTable(first_liberal_url+last_url)

    #専門科目のDataFrameを作成
    for special in specials:
        tmp_df = fetchInfoTable(first_special_url+special+last_url)
        df_special = pd.concat([df_special,tmp_df])

    driver.close()
    driver.quit()

    #データの整理
    df_liberal = df_liberal.iloc[:,0:4]
    df_liberal.columns =["time","subject","teacher","date"]

    df_special = df_special.iloc[:,0:5]
    df_special.columns =["time","subject","teacher","department","date"]

    #一つのDataFrameにまとめる
    df = pd.concat([df_liberal,df_special[["time","subject","teacher","date"]]])

    # df = df.reset_index(drop=True)
    change_time = lambda x: x[-2:-1]
    delete_time = lambda x : x[:-4]
    df["time"] = df["date"].apply(change_time)
    df["time"] = df["time"].astype(int)
    df["date"] = df["date"].apply(delete_time)
    df["date"] = pd.to_datetime(df["date"])
    df["date"] = df["date"].dt.date
    df["teacher"] = df["teacher"].str.replace("\n"," ")

    return df

#urlにあるテーブルデータを読み込みDataFrameを返す
def fetchInfoTable(url):
    df = pd.DataFrame()
    driver.get(url)

    #テーブルデータを取得
    for class_name in ["odd_normal","even_normal"]:
        elements = driver.find_elements_by_class_name(class_name)

        for e in elements:
            tds = e.find_elements_by_tag_name("td")
            data = []
            for td in tds:
                data.append(str(td.text))
            tmp_df = pd.DataFrame(data)
            df = df.append(tmp_df.T)

    return df

#canceled_date日のbegin限~5限目の休講情報のツイート文章をリストで返す
def createTweetMessages(df,canceled_date,begin):
    msgs = []
    data = []
    now_time = datetime.datetime.now().strftime("%H:%M")
    canceled_date_str = canceled_date.strftime("%m/%d")

    msg =  canceled_date_str +"の休講情報[{}]".format(now_time)

    for i in range(begin,6):
        #i限目のDataFrameを作成
        tmp_df = df[df["time"] == i]

        msg +="\n【{}限】\n".format(i)
        data = []

        #dataに休講情報を1行づつ格納する
        for index, row in tmp_df.iterrows():
            data.append("{}({})\n".format(row["subject"],row["teacher"]))

        #140字に入るだけのツイート分を作成しmsgsに格納する
        for j in range(len(data)):
            if len(msg) + len(data[j])  < 140:
                msg += data[j]
            else:
                msgs.append(msg)
                msg = canceled_date_str +"の休講情報[{}]".format(now_time)
                msg +="\n【{0}限続き】\n".format(i)
                msg += data[j]

    msgs.append(msg)
    return msgs

def postToTwitter(msg):
    if os.name == "nt":
        f = open("./twitter_account.json","r")
    else:
        f = open("/home/ec2-user/KUCancelAnnouncementBot/twitter_account.json","r")
    tw_ac = json.load(f)
    f.close()

    twitter = OAuth1Session(tw_ac['consumer_key'], tw_ac['consumer_secret'], tw_ac['access_token_key'], tw_ac['access_token_secret'])
    params = {"status": msg}

    try:
        req = twitter.post("https://api.twitter.com/1.1/statuses/update.json", params = params)
        print(req.text)
    except:
        print("can't post.")
        print(req.text)

def main():
    begin = sys.argv[1]     #1~5の場合その時限からの情報をpostする。6の場合は明日の休講情報をすべてpostする

    #休講情報を取得
    df = createInfoDF()

    today = datetime.date.today()

    if int(begin) == 6:
        tomorrow = today + datetime.timedelta(days = +1)
        use_df = df[df["date"] == tomorrow ]
        msgs = createTweetMessages(use_df,tomorrow,1)
    else:
        use_df  = df[df["date"] == today ]
        msgs = createTweetMessages(use_df,today,int(begin))

    for msg in msgs:
        postToTwitter(msg)

if __name__ == "__main__":
    main()
