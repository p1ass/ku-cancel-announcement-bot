from requests_oauthlib import OAuth1Session
from pathlib import Path
import json
import os

class TwitterClient:
    def __init__(self):
        # セッションを確立
        self.twitter = OAuth1Session(os.environ['CONSUMER_KEY'],
         os.environ['CONSUMER_SECRET'], 
         os.environ['ACCESS_TOKEN_KEY'], 
         os.environ['ACCESS_TOKEN_SECRET'])

    def post(self,msg):

        params = {"status": msg}

        try:
            req = self.twitter.post("https://api.twitter.com/1.1/statuses/update.json", params = params)
            # print(req.text)
        except:
            print("can't post.")
            print(req.text)
