# export_google_calender
指定した年月に対して、google calender apiを利用してカレンダー上の予定を取得し、カテゴリごとの所要時間の合計を日単位でまとめたcsvファイルとして出力します。


# 使い方
## 1. 環境構築
```bash
python -m venv .env
source .env/bin/activate
pip insrall -r requirements.txt
```

## 2. サービスアカウントの作成
[こちらのサイト](https://www.coppla-note.net/posts/tutorial/google-calendar-api/)などを参考にサービスアカウントの作成、キーの作成、アカウントへのカレンダーの共有を行う。
キーとして発行されたjsonファイルは`credentials.json`というファイル名で`conf/`に配置する。

## 3. 設定ファイルへの記述
`conf/config.yaml`に以下のようなフォーマットで設定を記述する。

```yaml
# カレンダーID
calender_id: "hogehoge@gmail.com"

# カテゴリとイベント（カレンダー上の予定のタイトル）の対応
event_categories:
  仕事:
    - 打合せ
    - 資料作成
    - 報告
  趣味:
    - ドライブ
    - ボルダリング
```

## 4. スクリプトの実行
```bash
# 引数を省略すると自動的に今の年月が設定される
python src/main.py --year 2023 --month 4
```
`main.py`を実行すると、`output/`に次の2つのcsvファイルが出力される。

### formatted_events.csv

各カテゴリごとに対応するイベントの所要時間の合計を日単位でまとめた表（othersはカテゴリが紐づかなかったイベントの所要時間の合計）
| date       | 仕事  | 趣味  | others | 
| ---------- | ----- | ----- | ------ | 
| 2023-04-01 | 02:00 |       | 00:30  | 
| 2023-04-02 |       | 03:00 |        | 
| 2023-04-03 | 03:30 | 01:30 | 03:00  | 

### events_without_category.csv

カテゴリが紐づかなかったイベント（上記のothersに含まれるものに対応）に対して、各イベントとその所要時間をまとめた表

| date       | event  | duration | 
| ---------- | ------ | -------- | 
| 2023-04-01 | 散歩   | 00:30    | 
| 2023-04-03 | カット | 00:30    | 
| 2023-04-03 | 飲み会 | 02:30    | 