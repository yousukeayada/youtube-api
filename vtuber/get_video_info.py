import os
import json
import datetime

import pandas as pd
from apiclient.discovery import build
import requests
from bs4 import BeautifulSoup
from retry import retry



YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

max_results = 50

def fetch_video_list(channel_id, max_results):
    response = youtube.search().list(
                    part="snippet", 
                    channelId=channel_id,
                    order="date", 
                    type="video",
                    eventType="none",
                    maxResults=max_results
                    ).execute()
    return response

def fetch_video_info(video_ids):
    response = youtube.videos().list(
                    part='liveStreamingDetails', 
                    id=video_ids,
                    ).execute()
    return response

def find_video_info(response):
    video_ids = []
    titles = []
    print(json.dumps(response))
    for r in response["items"]:
        # 配信中のものや動画は除く（live,upcoming）
        if r["snippet"]["liveBroadcastContent"] != "none":
            continue
        video_ids.append(r["id"]["videoId"])
        titles.append(r["snippet"]["title"].replace(",","、"))
    print(f"video_ids: {len(video_ids)}")

    response = fetch_video_info(video_ids)
    print(json.dumps(response))
    dates = []
    durations = []
    not_live = []
    for i, r in enumerate(response["items"]):
        if r.get("liveStreamingDetails") is None:
            not_live.insert(0, i)
            continue
        start_str = r["liveStreamingDetails"].get("actualStartTime")
        if start_str is None:
            continue
        end_str = r["liveStreamingDetails"].get("actualEndTime")
        start_dt = datetime.datetime.fromisoformat(start_str.replace("Z","+09:00"))
        end_dt = datetime.datetime.fromisoformat(end_str.replace("Z","+09:00"))
        # 配信開始日を求める（例：2021-01-15）
        td = datetime.timedelta(hours=9)
        dates.append((start_dt + td).date())
        durations.append((end_dt - start_dt).seconds)
    print(f"not live: {len(not_live)}")
    for i in not_live:
        video_ids.pop(i)
        titles.pop(i)
        
    return video_ids, titles, dates, durations


###############################################
############## continuation 取得 ###############
###############################################
class ContinuationURLNotFound(Exception):
    pass

class LiveChatReplayDisabled(Exception):
    pass

class RestrictedFromYoutube(Exception):
    pass

def get_ytInitialData(target_url, session):
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    html = session.get(target_url, headers=headers)
    soup = BeautifulSoup(html.text, 'html.parser')
    for script in soup.find_all('script'):
        script_text = str(script)
        if 'ytInitialData' in script_text:
            for line in script_text.splitlines():
                if 'ytInitialData' in line:
                    if 'var ytInitialData =' in line:
                        st = line.strip().find('var ytInitialData =') + 19
                        return json.loads(line.strip()[st:-10])
                    if 'window["ytInitialData"] =' in line:
                        return json.loads(line.strip()[len('window["ytInitialData"] = '):-1])

    if 'Sorry for the interruption. We have been receiving a large volume of requests from your network.' in str(soup):
        print("restricted from Youtube (Rate limit)")
        raise RestrictedFromYoutube

    return None

def check_livechat_replay_disable(ytInitialData):
    conversationBar = ytInitialData['contents'].get('twoColumnWatchNextResults',{}).get('conversationBar', {})
    if conversationBar:
        conversationBarRenderer = conversationBar.get('conversationBarRenderer', {})
        if conversationBarRenderer:
            text = conversationBarRenderer.get('availabilityMessage',{}).get('messageRenderer',{}).get('text',{}).get('runs',[{}])[0].get('text')
            print(text)
            if text == 'この動画ではチャットのリプレイを利用できません。':
                return True
    else:
        return True

    return False

@retry(ContinuationURLNotFound, tries=2, delay=1)
def get_initial_continuation(target_url):
    # print("target_url:", target_url)
    session = requests.session()
    try:
        ytInitialData = get_ytInitialData(target_url, session)
    except RestrictedFromYoutube:
        return None

    if not ytInitialData:
        print("Cannot get ytInitialData")
        raise ContinuationURLNotFound

    if check_livechat_replay_disable(ytInitialData):
        print("LiveChat Replay is disable")
        raise LiveChatReplayDisabled

    continue_dict = {}
    try:
        subMenuItems = ytInitialData['contents']['twoColumnWatchNextResults']['conversationBar']['liveChatRenderer']['header']['liveChatHeaderRenderer']['viewSelector']['sortFilterSubMenuRenderer']['subMenuItems']
        for continuation in subMenuItems:
            continue_dict[continuation['title']] = continuation['continuation']['reloadContinuationData']['continuation']
    except KeyError:
        print("Cannot find continuation")

    continue_url = None
    if not continue_url:
        if continue_dict.get('上位のチャットのリプレイ'):
            continue_url = continue_dict.get('上位のチャットのリプレイ')
        if continue_dict.get('Top chat replay'):
            continue_url = continue_dict.get('Top chat replay')
    
    if not continue_url:
        if continue_dict.get('チャットのリプレイ'):
            continue_url = continue_dict.get('チャットのリプレイ')
        if continue_dict.get('Live chat replay'):
            continue_url = continue_dict.get('Live chat replay')
    
    if not continue_url:
        continue_url = ytInitialData["contents"]["twoColumnWatchNextResults"].get("conversationBar", {}).get("liveChatRenderer",{}).get("continuations",[{}])[0].get("reloadContinuationData", {}).get("continuation")

    if not continue_url:
        raise ContinuationURLNotFound

    return continue_url

def check_initial_continuation(video_id):
    target_url = "https://www.youtube.com/watch?v=" + video_id
    # file_prefix = channel_id + '/' + video_id + '/'

    try:
        continuation = get_initial_continuation(target_url)
    except LiveChatReplayDisabled:
        print(video_id + " is disabled Livechat replay, create blank list")
        # print(file_prefix + 'blank.json' + ' saved')
        return None
    except ContinuationURLNotFound:
        print(video_id + " can not find continuation url")
        return None
    except Exception as e:
        print(e)
    else:
        return continuation



df = pd.read_csv("channel_info.csv")
for channel_id, channel_title in zip(df["channel_id"], df["title"]):
    print(channel_title)
    response = fetch_video_list(channel_id, max_results)
    # print(json.dumps(response))
    video_ids, titles, dates, durations = find_video_info(response)

    continuations = []
    for video_id in video_ids:
        continuation = check_initial_continuation(video_id)
        if not continuation:
            print("not continuation")
            continuation = ""
        continuations.append(continuation)

    with open(f"{channel_title}/video_info.csv", mode='w') as dist:
        dist.write("channel_id,channel_title,video_id,title,date,duration,continuation\n")
        
        print(len(dates))
        print(len(durations))
        print(len(continuations))
        for i in range(len(video_ids)):
            dist.write(f"{channel_id},{channel_title},{video_ids[i]},{titles[i]},{dates[i]},{durations[i]},{continuations[i]}\n")

