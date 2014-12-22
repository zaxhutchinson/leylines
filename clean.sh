#!/bin/bash

if [ "$1" = "all" ]
then
	rm -f $PWD/logs/*
	rm -f $PWD/profiles/*
	rm -f $PWD/*.pyc
	#rm -f $PWD/uid_list
else
	while read line
	do
		if [ "$1" = "${line}" ]
		then
			if [ -f "$PWD/profiles/$1" ]
			then
				rm "$PWD/scripts/$1"
			fi
		fi
	done <$PWD/profiles/uid_list
fi
