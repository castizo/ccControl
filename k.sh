#!/bin/sh
value=`cat mpd/pid`
echo "Killing mpd process with pid=$value"
kill -9 $value


