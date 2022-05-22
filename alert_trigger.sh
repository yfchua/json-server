#!/bin/bash

# alert_trigger.sh [hostname] [disk|cpu|mem] <options>

if [ "$#" -lt 2 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

action=$2
host=$1
option=$3

case $action in
	disk)
		df -kl $option 2>&1 > /tmp/do.$$
		echo "=============================" >> /tmp/do.$$
		du -x -d 1 -ak $option 2>&1 >> /tmp/do.$$
		e=0
		;;
	cpu)
                top -d 2 -n 2 -o %CPU 2>&1 > /tmp/co.$$
		e=0
		;;
	mem)
		top -d 2 -n 2 -o %MEM 2>&1 > /tmp/mo.$$
		e=0
		;;
	*)
		e=1
		;;
esac
exit $e
