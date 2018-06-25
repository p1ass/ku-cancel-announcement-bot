from requests_oauthlib import OAuth1Session
import json

class TwitterManager:
    def __init__(self,path):

        #API情報を読み込む
        f = open(path,"r")
        self.twitter_account = json.load(f)
        f.close()

        #セッションを確立
        self.twitter = OAuth1Session(self.twitter_account['consumer_key'], self.twitter_account['consumer_secret'], self.twitter_account['access_token_key'], self.twitter_account['access_token_secret'])

    def post(self,msg):

        params = {"status": msg}

        try:
            req = self.twitter.post("https://api.twitter.com/1.1/statuses/update.json", params = params)
            # print(req.text)
        except:
            print("can't post.")
            print(req.text)
