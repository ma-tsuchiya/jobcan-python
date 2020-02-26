# jobcan-python

seleniumを用いてjobcanを操作するライブラリです.
まだ未完成ですが、結構動くとおもいます。

# licence

自由に使ってください。ライセンス等の表記も不要です。
このライブラリを利用したことによる損害について、作成者は一切の責任を負いません。

# requirements
- python3
- selenium
- chromedriver


# setup
settingファイルを作成し, user_email, user_password, chromedriver_pathを設定してください.
作成は, setting.sampleを参考にしてください。

# usage
ログイン
```python
from jobcan import Jobcan
jobcan = Jobcan()           # settingファイルを作成してある場合, これでログインできます.
```
出勤
```
jobcan.start_job('本社')    #　勤務開始の打刻をします. 夜勤モード非対応です.
```
退勤
```python
jobcan.end_job()            #　勤務終了の打刻をします. 夜勤モード非対応です. 日をまたがずに帰ってください.
```

工数入力
```python
jobcan.add_man_hour(self, project_name='不毛な会議', task_name='出席', year=2020, month=1, day=3, worktime_hour=2, worktime_minute=15)         # 工数入力をします.
```
# todo

- 工数入力の労働時間・工数の一致確認処理実装
- サンプルコードの作成
- 参考サイト
