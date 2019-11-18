# KU休講情報Bot
京都大学の休講情報をTwitterに呟くBotです。([@KUKyukoBot](https://twitter.com/KUKyukoBot))

以前から同じ名前のTwitterアカウント([@ku_kyukou_bot](https://twitter.com/ku_kyukou_bot))が存在していましたが、運営の方が卒業され止まったままだったので、
その機能を引き継ぎました。


## 使い方
Dockerイメージを使って起動することができます。


1. Dockerイメージをpullする。
```bash
docker pull plass/ku-cancel-announcement:latest
``` 

2. `.env.example`を参考に環境変数を定義した`.env`ファイルを作る。

3. 実行
```bash
docker run -it --rm  --env-file=.env  plass/ku-cancel-announcement-bot [N]
```

**パラメータ**
- n : n限目-5限目までの情報をつぶやきます。6を指定した場合は明日の情報を1限目-5限目までつぶやきます。

## Lisence
MIT

## Contribution

1. [このリポジトリ](https://github.com/naoki-kishi/ku-cancel-announcement-bot)をフォークする。
2. フォーク先のリポジトリでトピックブランチを作り、コミットする。
```bash
git checkout -b topic_branch
```
3. [naoki-kishi/ku-cancel-announcement-bot](https://github.com/naoki-kishi/ku-cancel-announcement-bot)対してPull Requestを作成する。
