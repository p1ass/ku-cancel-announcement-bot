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

#一般教養科目の休講情報を取得しdfで返す
def create_df():
    #アカウント情報を取得
    if os.name == "nt":
        f = open("./account.json","r")
    else:
        f = open("/home/ec2-user/KUCancelAnnouncementBot/account.json","r")
    account = json.load(f)
    f.close()


    liberal_url = "https://www.k.kyoto-u.ac.jp/student/la"
    special_url = "https://www.k.kyoto-u.ac.jp/student/u/"
    last_url = "/notice/cancel"
    specials = ["let","ed","l","ec","s","med","medh","p","t","a","h",]

    #まず全共のページに行く際にログイン処理をする
    driver.get(liberal_url+last_url)
    driver.find_element_by_id("username").send_keys(account["ecs-id"])
    driver.find_element_by_id("password").send_keys(account["password"])
    driver.find_element_by_name("_eventId_proceed").click()


    #DataFrameを作成
    df = pd.DataFrame()
    df_liberal = pd.DataFrame()
    df_special = pd.DataFrame()

    #全学共通科目のdfを作成
    df_liberal = get_table(liberal_url+last_url)

    #専門科目のdfを作成
    for special in specials:
        tmp_df = get_table(special_url+special+last_url)
        df_special = pd.concat([df_special,tmp_df])

    driver.close()
    driver.quit()
    print(len(df_special.columns))
    #データの整理
    df_liberal = df_liberal.iloc[:,0:4]
    df_liberal.columns =["time","subject","teacher","date"]

    df_special = df_special.iloc[:,0:5]
    df_special.columns =["time","subject","teacher","department","date"]

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

#テーブルデータからdfを作成
def get_table(url):
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

#date日のnow限以降の休講情報のツイート文章をリストで返す
def create_messages(df,date,now):
    msgs = []
    data = []
    now_time = datetime.datetime.now().strftime("%H:%M")
    msg =  date.strftime("%m/%d")+"の休講情報[{}]".format(now_time)

    for i in range(now,6):
        tmp_df = df[df["time"] == i]
        msg +="\n【{}限】\n".format(i)
        data = []

        for index, row in tmp_df.iterrows():
            data.append("{}({})\n".format(row["subject"],row["teacher"]))

        for j in range(len(data)):

            if len(msg) + len(data[j])  < 140:
                msg += data[j]
            else:
                msgs.append(msg)
                msg = date.strftime("%m/%d")+"の休講情報(続き)[{}]".format(now_time)
                msg +="\n【{0}限】\n".format(i)
                msg += data[j]
    msgs.append(msg)
    return msgs

#msgで渡されたstringをツイッターに投稿する
def post_to_twitter(msg):
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
    #コマンドライン引数を取得
    #1~5の場合その時限からの情報をpostする。6の場合は明日の休講情報をすべてpostする
    argvs = sys.argv


    #休講情報を取得
    df = create_df()

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days = +1)

    #引数によって使うdfを絞り、メッセージを作成
    if int(argvs[1]) == 6:
        use_df = df[df["date"] == tomorrow ]
        msgs = create_messages(use_df,tomorrow,1)
    else:
        use_df  = df[df["date"] == today ]
        msgs = create_messages(use_df,today,int(argvs[1]))

    #post
    for msg in msgs:
        post_to_twitter(msg)

if __name__ == "__main__":
    main()
