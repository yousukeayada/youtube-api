import os
import sys
import json
import datetime

import requests
import pandas as pd


headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
# continuation = "op2w0wR0GmxDamdhRFFvTFdsRnVXbms1WlU5TFpqZ3FKd29ZVlVNemJFNUdaVXBwVkhFMlRETlZWMjk2TkdjeFpTMUJFZ3RhVVc1YWVUbGxUMHRtT0JvVDZxamR1UUVOQ2d0YVVXNWFlVGxsVDB0bU9DQUJAAXICCAQ%3D"

def fetch_json():
    print("fetch_json()",file=sys.stderr)
    url = "https://www.youtube.com/live_chat_replay?continuation=" + continuation
    res = requests.get(url, headers=headers)
    lines = res.text.splitlines() #改行区切り
    json_text = ""
    # with open("jsn.json", mode='w') as f:
        
    for l in lines: #json部分を抜き出す
        # f.write(l)
        pos = l.find("{\"responseContext")
        if pos > 0:
            json_text = l[pos:len(l)-1]

    if json_text == "":
        print("json_text is None",file=sys.stderr)
        jsn = fetch_json()
        return jsn
    
    
    try:
        jsn = json.loads(json_text)
        print(type(jsn),file=sys.stderr)
        
        return jsn
    except json.JSONDecodeError as e:
        print(sys.exc_info(),file=sys.stderr)
        print("JSONDecodeError",file=sys.stderr)
        fetch_json()
    


def parse_json():
    global jsn
    print("parse_json()",file=sys.stderr)
    # print("jsn=",jsn,file=sys.stderr)
    if jsn is None:
        print("jsn is None",file=sys.stderr)
        jsn = fetch_json()
    actions = jsn.get("continuationContents").get("liveChatContinuation").get("actions")
    if actions is None:
        print("actions is None",file=sys.stderr)
        # exit(0)
    else:
        for j in actions:
            addChatItemAction = j["replayChatItemAction"]["actions"][0].get("addChatItemAction")
            if addChatItemAction != None:
                # print(addChatItemAction)
                liveChatTextMessageRenderer = addChatItemAction["item"].get("liveChatTextMessageRenderer")
                if liveChatTextMessageRenderer != None:
                    timestamp = liveChatTextMessageRenderer["timestampText"]["simpleText"]
                    authorName = liveChatTextMessageRenderer["authorName"]["simpleText"]
                    authorBadges = liveChatTextMessageRenderer.get("authorBadges")
                    if authorBadges != None:
                        tooltip = authorBadges[0]["liveChatAuthorBadgeRenderer"]["tooltip"]
                        membership = tooltip
                        # メンバー（10 か月）などもあるので以下では捕捉しきれない
                        # if tooltip == "新規メンバー":
                        #     membership = 1
                        # elif tooltip == "メンバー（1 か月）":
                        #     membership = 2
                        # elif tooltip == "メンバー（2 か月）":
                        #     membership = 3
                        # elif tooltip == "メンバー（6 か月）":
                        #     membership = 4
                        # elif tooltip == "メンバー（1 年）":
                        #     membership = 5
                        # elif tooltip == "メンバー（2 年）":
                        #     membership = 6
                        # else:
                        #     membership = -1
                    else:
                        membership = "非メンバー"
                    runs = liveChatTextMessageRenderer["message"]["runs"]
                    text = ""
                    for r in runs:
                        if r.get("text") is None:
                            text += r["emoji"]["shortcuts"][0]
                        else:
                            text += r["text"]

                    with open(chat_replay_file, mode="a") as f:
                        # CSV の列数を崩さないように「,」を置換する
                        f.write(f"{timestamp},{authorName.replace(',','_')},{membership},{text.replace(',','_')}\n")
                    # print(f"{timestamp},{authorName},{member},{msg}")
                else:
                    print("not liveChatTextMessageRenderer",file=sys.stderr)
            else:
                print("not addChatItemAction",file=sys.stderr)


def fetch_chat_replay():
    global continuation, jsn, chat_replay_file
    df = pd.read_csv(f"{channel_title}/video_info.csv")
    for video_id, title, date, continuation in zip(df["video_id"], df["title"], df["date"], df["continuation"].fillna("")):
        print(f"{title},{date},{continuation}")
        # 2020年12月分のみ取得する
        date_dt = datetime.date.fromisoformat(date)
        if date_dt.year != 2020 or date_dt.month != 12:
            print("invalid date")
            continue
        if not continuation:
            print("chat replay is not exists")
            continue
        chat_replay_file = f"{channel_title}/chat_replay_{video_id}.csv"
        if os.path.exists(chat_replay_file):
            print(f"{chat_replay_file} already exists, so remove it.")
            os.remove(chat_replay_file)
        with open(chat_replay_file, mode="w") as f:
            f.write("timestamp,author_name,membership,text\n")
        count = 1
        jsn = None
        while True:
            if not continuation:
                print("not continuation. next video")
                break
            jsn = fetch_json()
            if jsn is None:
                print("jsn=",jsn,file=sys.stderr)
            else:
                print("jsn is not None",file=sys.stderr)
            parse_json()
            if jsn is None:
                print("jsn=",jsn,file=sys.stderr)
            else:
                # print(jsn)
                liveChatReplayContinuationData = jsn.get("continuationContents").get("liveChatContinuation").get("continuations")[0].get("liveChatReplayContinuationData")
                if liveChatReplayContinuationData:
                    continuation = liveChatReplayContinuationData.get("continuation")
                else:
                    continuation = None
            print(count," : continuation = ",continuation, file=sys.stderr)
            count += 1


# channel_title = "Shizuka Rin Official"
# fetch_chat_replay()
df = pd.read_csv(f"channel_info.csv")
for channel_title in df["title"]:
    print(channel_title)
    fetch_chat_replay()
