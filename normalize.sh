#!/bin/bash

for i in `lpass ls | grep id | awk '{print $NF}' | sed 's/\]//'`;
do
    url=$(lpass show --url $i)
    if echo $url | grep -q "^http://"; then
        new=$(echo $url | sed 's@^http://@https://@')
        echo "update $i url to $new"
        echo "URL: $new" | lpass edit --non-interactive --sync=now $i
    fi
done
