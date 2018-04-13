#!/bin/sh
for python_file in `ls ./*.py`
do
    /usr/local/bin/python $python_file &
done
while true
do
    sleep 10
done