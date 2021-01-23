#!/bin/bash

# ./find_col_miss.sh "ディレクトリ名"

set -euo pipefail

# このスクリプト自身のディレクトリに移動する
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"


dir="${1}"

ls "${dir}" | while read line;
do 
    echo "${line}"
    cat "${dir}/${line}" | awk '        
        BEGIN{
            FS = ","
        }
        {
            if(NF != 4){
                {print NR ": ", $0}
            }
        }
    '
done
