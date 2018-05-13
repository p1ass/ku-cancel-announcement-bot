from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import pandas as pd
import datetime
import time
from requests_oauthlib import OAuth1Session
import sys

#一般教養科目の休講情報を取得しdfで返す
def get_table():
    #アカウント情報を取得
    f = open("/home/ec2-user/KUCancelAnnouncementBot/account.json","r")
    account = json.load(f)
    f.close()

    #ログイン処理
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,1024')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get("https://www.k.kyoto-u.ac.jp/student/la/notice/cancel")
    driver.find_element_by_id("username").send_keys(account["ecs-id"])
    driver.find_element_by_id("password").send_keys(account["password"])
    driver.find_element_by_name("_eventId_proceed").click()


    #DataFrameを作成
    df = pd.DataFrame()

    #テーブルデータを取得
    elements = driver.find_elements_by_class_name("odd_normal")
    for e in elements:
        tds = e.find_elements_by_tag_name("td")
        data = []
        for td in tds:
            data.append(str(td.text))
        tmp_df = pd.DataFrame(data)
        df = df.append(tmp_df.T)

    elements = driver.find_elements_by_class_name("even_normal")
    for e in elements:
        tds = e.find_elements_by_tag_name("td")
        data = []
        for td in tds:
            data.append(str(td.text))
        tmp_df = pd.DataFrame(data)
        df = df.append(tmp_df.T)

    driver.close()
    driver.quit()

    #データの整理
    df = df.iloc[:,0:4]
    df.columns =["time","subject","teacher","date"]
    df = df.reset_index(drop=True)
    change_time = lambda x: x[-2:-1]
    delete_time = lambda x : x[:-4]
    df["time"] = df["date"].apply(change_time)
    df["time"] = df["time"].astype(int)
    df["date"] = df["date"].apply(delete_time)
    df["date"] = pd.to_datetime(df["date"])
    df["date"] = df["date"].dt.date
    df["teacher"] = df["teacher"].str.replace("\n"," ")

    return df

#date日のnow限以降の休講情報のツイート文章をリストで返す
def create_messages(df,date,now):
    msgs = []
    data = []
    msg =  date.strftime("%m/%d")+"の休講情報"

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
                msg = date.strftime("%m/%d")+"の休講情報(続き)"
                msg +="\n【{0}限】\n".format(i)
                msg += data[j]
    msgs.append(msg)
    return msgs

#msgで渡されたstringをツイッターに投稿する
def post_to_twitter(msg):
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
    df = get_table()

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
