#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import re
import json
import time
import threading
from influxdb import InfluxDBClient
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
config_file = open('config.json')
config = json.load(config_file, encoding='utf-8')
config_file.close()
client = InfluxDBClient(config['influxdb_ip'], config['influxdb_port'], config['influxdb_username'], config['influxdb_passwd'], config['influxdb_db'])
ignore_container_list = config['ignore_container_list']
container_logs_path = config['container_logs_path']
container_config_file = config['container_config_file_name']
sleep_time = config['sleep_time']
def escape_ansi(line):
    try:
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)
    except BaseException,e:
        print "logs_collector.py-->escape_ansi-->%s" %e
        return
def get_container_config_file(path, container_config_file):
    try:
        file_list = []
        for dirpath,dirnames,filenames in os.walk(path):
            for name in filenames:
                if name == container_config_file:
                    file_list.append(os.path.join(dirpath, name))
        return file_list
    except BaseException,e:
        print "logs_collecotr.py-->get_container_config_file-->%s" %e
        return
def read_file(container_config_file):
    try:
        f = open(container_config_file)
        data = json.load(f, encoding='utf-8')
        f.close()
        container_name = data['Name'][1:]
        if container_name in ignore_container_list:
            return
        tags = {}
        container_id = data['ID'][:12]
        log_path = data['LogPath']
        container_image = data['Config']['Image']
        tags['container_id'] = container_id
        tags['container_name'] = container_name
        tags['container_image'] = container_image
        if os.path.isfile(log_path):
            logs = open(log_path)
            logs.seek(0, 2)
            while 1:
                if os.path.isfile(log_path):
                    where = logs.tell()
                    line = logs.readline()
                    if not line:
                        time.sleep(sleep_time)
                        logs.seek(where)
                    else:
                        log_json = json.loads(escape_ansi(line))
                        content = log_json['log'].strip()
                        client.write_points([{"measurement": 'logs', "tags": tags, "fields": {"value": content}}])
                else:
                    logs.close()
    except BaseException,e:
        print "logs_collector.py-->read_file-->%s" %e
    finally:
        return
try:
    log_list = get_container_config_file(container_logs_path, container_config_file)
    for log_name in log_list:
        t = threading.Thread(target=read_file, args=(log_name,))
        t.setDaemon(True)
        t.start()
except BaseException,e:
    print "logs_collector.py-->log_list-->%s" %e
while True:
    try:
        log_list_new = get_container_config_file(container_logs_path, container_config_file)
        removed_container = list(set(log_list).difference(set(log_list_new)))
        for item in removed_container:
            log_list.remove(item)
        new_container = list(set(log_list_new).difference(set(log_list)))
        for log_name in new_container:
            t = threading.Thread(target=read_file, args=(log_name,))
            t.setDaemon(True)
            t.start()
        for new_item in new_container:
            log_list.append(new_item)
    except BaseException,e:
        print "logs_collector.py-->while True-->%s" %e
    finally:
        time.sleep(sleep_time)