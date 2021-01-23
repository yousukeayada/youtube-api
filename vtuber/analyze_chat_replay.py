import sys
import datetime
import csv

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
from statistics import mean, stdev


try: # python analyze_chat_replay.py 0 でログを出力しない
    enable_log = int(sys.argv[1])
except:
    enable_log = True
def printerr(msg):
    if enable_log:
        print(msg, file=sys.stderr)

def get_h_m_s(s):
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return h, m, s

def plot_pie(data):
    # 円グラフ作成
    # plt.style.use("bmh")
    label = ["非メンバー","新規メンバー","1か月","2か月","6か月","1年","2年"]
    for i in range(7): # 0人は省く
        if data[6-i] == 0:
            label.pop(6-i)
            data.pop(6-i)
    cmap = plt.get_cmap("Set3")
    colors = cmap(np.arange(len(label)))
    plt.pie(data, counterclock=False, startangle=90, 
            autopct=lambda p:f'{p:.2f}%' if p>=2 else '', 
            pctdistance=0.8, radius=1.5, 
            colors=colors,
            textprops={'color': "black", 'weight': "bold"})
    plt.legend(label, title="Member type", bbox_to_anchor=(1, 0, .5, 1))
    plt.savefig(f"{directory}/202012.png",bbox_inches="tight")
    # plt.show()
    plt.clf()
    plt.close()


def make_fixed_period_list():
    # 2020年12月分のみのリストを作成する
    video_ids = []
    titles    = []
    dates     = []
    durations = []
    durations_hms = []
    for vid, title, date, duration, con in zip(video_info["video_id"], video_info["title"], video_info["date"], video_info["duration"], video_info["continuation"].fillna("")):
        date_dt = datetime.date.fromisoformat(date)
        if date_dt.year != 2020 or date_dt.month != 12:
            printerr(f"{vid}: invalid date")
            continue
        if con == "":
            printerr(f"{vid}: chat replay is none")
            continue
        video_ids.append(vid)
        titles.append(title)
        dates.append(date)
        durations.append(duration)
        h,m,s = get_h_m_s(duration)
        durations_hms.append(f"{h}h {m}m {s}s")

    # 配信回数、配信時間
    num_streams_list.append(len(video_ids))
    sum_durations_list.append(sum(durations))
    h,m,s = get_h_m_s(sum(durations))
    sum_durations_hms_list.append(f"{h}h {m}m {s}s")

    # コメントの集計
    num_comments = []
    num_accounts = []
    num_members  = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[]}
    for vid in video_ids:
        # quoting= でエラー回避
        df = pd.read_csv(f"{directory}/chat_replay_{vid}.csv", usecols=["author_name", "membership"], quoting=csv.QUOTE_NONE)

        # 総コメント数
        num_comments.append(len(df))

        # コメントした人数
        df2 = df.drop_duplicates(subset='author_name')
        num_accounts.append(len(df2))

        # コメントした人のタイプ別割合
        num_member = {}
        for i in range(7):
            num_member[i] = 0
        for membership in df2["membership"]:
            # print(type(m))
            m = str(membership)
            if "非" in m or "確認済み" in m or "モデレーター" in m or "所有者" in m:
                num_member[0] += 1
            elif "2 年" in m:
                num_member[6] += 1
            elif "1 年" in m:
                num_member[5] += 1
            elif "新規" in m:
                num_member[1] += 1
            else:
                if "メンバー（1 か月）" in m:
                    num_member[2] += 1
                elif "メンバー（2 か月）" in m:
                    num_member[3] += 1
                else: # 2-6 か月
                    num_member[4] += 1
        for i in range(7):
            num_members[i].append(num_member[i])

    # 新たに列を追加してCSVに書き出す
    video_info_new = pd.DataFrame({'video_id'    : video_ids,
                                   'title'       : titles,
                                   'date'        : dates,
                                   'duration'    : durations,
                                   'duration_hms': durations_hms,
                                   'num_comments': num_comments,
                                   'num_accounts': num_accounts,
                                  })
    video_info_new["cps"] = video_info_new["num_comments"] / video_info_new["duration"]
    for i in range(7):
        video_info_new[f"num_members{i}"] = num_members[i]
    video_info_new.to_csv(f"{directory}/video_info_new.csv", index=False)


    # 結果出力
    pct_members = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[]}
    for i in range(len(video_ids)):
        printerr(f"{titles[i]}({video_ids[i]})")
        printerr(f"コメント数: {num_comments[i]}")
        printerr(f"コメントした人数: {num_accounts[i]}")
        printerr(f"タイプ別割合")
        for j in range(7):
            printerr(f"   {j}: {num_members[j][i]*100/num_accounts[i]:.3f} %,{num_members[j][i]}")
            pct_members[j].append(num_members[j][i]*100/num_accounts[i])

    # 合計、平均、標準偏差
    mean_members = []
    sum_comments = sum(num_comments)
    sum_accounts = sum(num_accounts)
    mean_comments = mean(num_comments) if len(video_ids) > 0 else 0
    mean_accounts = mean(num_accounts) if len(video_ids) > 0 else 0
    stdev_comments = stdev(num_comments) if len(video_ids) > 1 else 0
    stdev_accounts = stdev(num_accounts) if len(video_ids) > 1 else 0
    printerr(f"総コメント数: {sum_comments},{mean_comments:.3f},{stdev_comments:.3f}")
    printerr(f"コメントした人数: {sum_accounts},{mean_accounts:.3f},{stdev_accounts:.3f}")
    for i in range(7):
        mean_pct_members = mean(pct_members[i]) if len(video_ids) > 0 else 0
        mean_members.append(mean_pct_members)
        stdev_pct_members = stdev(pct_members[i]) if len(video_ids) > 1 else 0
        printerr(f"   {i}: {mean_pct_members:.3f} %,{stdev_pct_members:.3f}")

    sum_comments_list.append(sum_comments)
    sum_accounts_list.append(sum_accounts)
    stdev_comments_list.append(stdev_comments)
    stdev_accounts_list.append(stdev_accounts)
    for i in range(7):
        mean_members_list[i].append(mean_members[i])

    plot_pie(mean_members)


channel_info = pd.read_csv("channel_info.csv")
result_analysis = pd.DataFrame({"channel_title"   : channel_info["title"],
                                "subscriber_count": channel_info["subscriber_count"],
                               })
num_streams_list       = []
sum_durations_list     = []
sum_durations_hms_list = []
sum_comments_list      = []
sum_accounts_list      = []
stdev_comments_list    = []
stdev_accounts_list    = []
mean_members_list      = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]}

prefix = "."
# メインループ
for channel_title, subscriber_count in zip(channel_info["title"], channel_info["subscriber_count"]):
    print(channel_title)
    directory = f"{prefix}/{channel_title}"
    video_info = pd.read_csv(f"{directory}/video_info.csv")
    make_fixed_period_list()
    
# 最終結果をCSVに出力
result_analysis["num_streams"]       = num_streams_list
result_analysis["sum_durations_s"]   = sum_durations_list
result_analysis["sum_durations_hms"] = sum_durations_hms_list
result_analysis["sum_comments"]      = sum_comments_list
result_analysis["sum_accounts"]      = sum_accounts_list
result_analysis["cps"]               = result_analysis["sum_comments"] / result_analysis["sum_durations_s"]
result_analysis["mean_accounts"]     = result_analysis["sum_accounts"] / result_analysis["num_streams"]
result_analysis["stdev_comments"]    = stdev_comments_list
result_analysis["stdev_accounts"]    = stdev_accounts_list
for i in range(7):
    result_analysis[f"mean_members{i}"] = mean_members_list[i]
result_analysis.to_csv("202012.csv", index=False)


# テスト用
# prefix = "."
# channel_title = "花畑チャイカ"
# directory = f"{prefix}/{channel_title}"
# video_info = pd.read_csv(f"{directory}/video_info.csv")
# make_fixed_period_list()
