from selenium import webdriver
import json
import pandas as pd
#アカウント情報を取得
f = open("account.json","r")
account = json.load(f)
f.close()

#ログイン処理
driver = webdriver.Chrome()
driver.get("https://www.k.kyoto-u.ac.jp/student/la/notice/cancel")
driver.find_element_by_id("username").send_keys(account["ecs-id"])
driver.find_element_by_id("password").send_keys(account["password"])
driver.find_element_by_name("_eventId_proceed").click()


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

#ブラウザを停止する
driver.close()
driver.quit()

#DataFrameの整理
change_time = lambda x: x[-3:-1]
delete_time = lambda x : x[:-4]
df["time"] = df["date"].apply(change_time)
df["date"] = df["date"].apply(delete_time)
df["date"] = pd.to_datetime(df["date"])

print(df)
