#!/bin/bash

set -euo pipefail

# このスクリプト自身のディレクトリに移動する
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"


ENDPOINT="https://www.googleapis.com/youtube/v3/channels"
API_KEY="${YOUTUBE_API_KEY}"

# channel_id="UC3lNFeJiTq6L3UWoz4g1e-A"
function list_channels() {
    channel_id=${1}
    URL="${ENDPOINT}?key=${API_KEY}&part=snippet,statistics&id=${channel_id}"
    res=$(curl ${URL})
}

# チャネルID、チャネル名、登録者数を出力
echo "channel_id,title,subscriber_count"
while read channel_id;
do
    list_channels ${channel_id}
    title=$(echo "${res}" | jq -r ".items[].snippet.title" | sed -e "s/\//_/g")
    subscriber_count=$(echo "${res}" | jq -r ".items[].statistics.subscriberCount")
    echo "${channel_id},${title},${subscriber_count}"
    # mkdir -p "${title}"
done < channel_id

# list_channels


exit 0
