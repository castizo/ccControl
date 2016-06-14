#!/bin/bash
#deploy

remote_machine="192.168.0.55"
#remote_machine="castizer.local"

if [ "$1" == up ]; then
  echo "Uploading changes to the server..."
  # Run this script to upload the remote folder
  # Inside castizer, the code is under: /
  rsync -rtvuc --delete ./src/ root@$remote_machine:/root/castizer-control/src/
  rsync -rtvuc --delete ./golden_configuration/ root@$remote_machine:/root/castizer-control/golden_configuration/
  rsync -rtvuc --delete ./run.py root@$remote_machine:/root/castizer-control/
  rsync -rtvuc --delete ./update/ root@$remote_machine:/root/castizer-control/update/
  rsync -rtvuc --delete ./mpd/playlists/ root@$remote_machine:/root/castizer-control/mpd/playlists/
  #rsync -rtvuc ./audiofiles/ root@$remote_machine:/root/castizer-control/audiofiles/
  echo "Done"
elif [ "$1" == down ]; then
  echo "Downloading updates from server..."
  rsync -rtvuc --delete root@$remote_machine:/root/castizer-control/src/ ./src/ 
  rsync -rtvuc --delete root@$remote_machine:/root/castizer-control/run.py .
#elif [ "$1" == pack ]; then
#  echo "Creating a tar package..."
#  rm -rf /tmp/castizer-control-package
#  cp -r ../castizer-control /tmp/castizer-control-package
#  rm -rf /tmp/castizer-control-package/audiofiles
#  current_dir=$PWD
#  cd /tmp
#  tar -cvf castizer-control-package.tar castizer-control-package
#  cd $current_dir
#  echo "Uploading the package to the server..."
#  scp /tmp/castizer-control-package.tar pgarcia@pc-pablo.dacya.ucm.es:/home/pgarcia
#  echo "Uploading the audio files to the castizer..."
#  rsync -rtvuc --delete /home/d/music root@$remote_machine:/root/castizer-control/audiofiles
#  echo "Done"
elif [ "$1" == overwrite ]; then
  echo "Overwriting changes to the server..."
  scp -r ./golden_configuration root@$remote_machine:/root/castizer-control/
  scp -r ./src root@$remote_machine:/root/castizer-control/
  scp ./run.py root@$remote_machine:/root/castizer-control/
  scp -r ./update root@$remote_machine:/root/castizer-control/
  scp -r ./mpd/playlists root@$remote_machine:/root/castizer-control/mpd/
  echo "Done"
else
  echo "Select action! (up/down)"
fi      


## Script to download the remote folder
#rsync -rtvuc --delete root@192.168.1.19:/usr/lib/lua/ ./src/


