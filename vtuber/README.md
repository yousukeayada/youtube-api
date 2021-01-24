- [にじさんじライバーの配信中のチャットを分析してみた](https://note.com/you0832/n/ne85768f9c817)

|        filename           |     description                                                                    |
|---------------------------|------------------------------------------------------------------------------------|
| `get_channel_info.sh`     | `channel_id`からチャンネルに関する情報を取得する。APIキーが必要。                          |
| `get_video_info.py`       | `channel_info.csv`から配信に関する情報を取得して`video_info.csv`に書き出す。APIキーが必要   |
| `get_chat_replay_info.py` | `video_info.csv`からチャットリプレイを取得して`chat_replay_{video_id}.csv`に書き出す。    |
| `find_col_miss.sh`        | チャットリプレイのCSVファイルが正常か確認する。列数が誤っている行を出力する。                  |
| `analyze_chat_replay.py`  | 集計したデータを加工して新しいCSVファイルに書き出す。                                      |
