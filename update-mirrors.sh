#!/bin/bash

mirror_dir=/home/git/mirrors
mirror_file=/home/git/mirrors.txt

cd $mirror_dir

echo "Updating mirrors [$(date)]"

while IFS="" read -r line || [ -n "$p" ]
do
	reponame=$(echo $line | awk -F "/" '{print $NF}')
	if [[ "$reponame" != *.git ]]
	then
		reponame="${reponame}.git"
	fi

	if [ ! -d $reponame ]
	then
		echo "Cloning ${reponame}..."
		git clone --mirror $line
	else
		echo "Updating ${reponame}..."
		cd $reponame
		git fetch -q --tags --no-show-forced-updates
		cd ..
	fi
done < $mirror_file

echo "Done updating mirrors [$(date)]"
