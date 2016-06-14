#!/bin/sh

update_folder="./update_package"
update_flag="./update"


TODAY=$(date)
echo "-----------------------------------------------------"
echo "Date: $TODAY"
echo "-----------------------------------------------------"

echo ">>> BEGIN updater script"
echo ">>> Checking local drive looking for updates..."

if [ ! -f "$update_flag" ]
then
    echo ">>> The system is up to date";
    exit 0;
fi

echo ">>> There is a new update."

echo ">>> Updating..."

current_folder=${PWD}
cd $update_folder
sh ./install.sh
exitCode=$?
echo ">>> Update completed. Exit code:" $exitCode
echo ">>> FINISHED!"
cd $current_folder

echo ">>> Deleting update flag..."
rm $update_flag
echo ">>> Deleting update folder..."
rm -rf $update_folder
echo ">>> Updating version number..."
mv next_version current_version

echo ">>> END updater script"

