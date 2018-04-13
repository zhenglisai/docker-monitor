#!/usr/bin/env python
# -*- coding:utf-8 -*-
import docker
import psutil
import json
from influxdb import InfluxDBClient
import time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
config_file = open('config.json')
config = json.load(config_file, encoding='utf-8')
config_file.close()
conn = docker.DockerClient(base_url='unix://var/run/docker.sock')
client = InfluxDBClient(config['influxdb_ip'], config['influxdb_port'], config['influxdb_username'], config['influxdb_passwd'], config['influxdb_db'])
eth_name = config['eth_name']
sleep_time = config['sleep_time']
while True:
    try:
        tags = {}
        tags['name'] = conn.info()['Name']
        try:
            tags['ip'] = psutil.net_if_addrs()[eth_name][0][1]
        except:
            tags['ip'] = "NULL"
        for event_data in conn.events():
            event = json.loads(event_data)
            points = []
            for key in event:
                key_point = [{"measurement": 'event_%s' %key, "tags": tags, "fields": {"value": str(event[key])}}]
                points.append(key_point)
            for point in points:
                client.write_points(point)
    except BaseException,e:
        print "event_collector.py-->while True-->：%s" %e
    time.sleep(sleep_time)