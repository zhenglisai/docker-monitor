#!/usr/bin/env python
# -*- coding:utf-8 -*-
import docker
import threading
import time
from influxdb import InfluxDBClient
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
config_file = open('config.json')
config = json.load(config_file, encoding='utf-8')
config_file.close()
sleep_time = config['sleep_time']
conn = docker.DockerClient(base_url='unix://var/run/docker.sock')
client = InfluxDBClient(config['influxdb_ip'], config['influxdb_port'], config['influxdb_username'], config['influxdb_passwd'], config['influxdb_db'])
def get_stats(container_obj):
    try:
        stats = container_obj.stats(stream=False)
        stats['image'] = container_obj.image
        container_stats_list.append(stats)
    except BaseException,e:
        print "docker_collector.py-->get_stats-->%s" %e
    finally:
        return
def calculate(container):
    try:
        points = []
        tags = {}
        tags['type'] = 'container'
        tags['id'] = container['id'][:12]
        tags['name'] = container['name'][1:]
        tags['image'] = container['image']
        # cpu percent
        previousCPU = container['precpu_stats']['cpu_usage']['total_usage']
        previousSystem = container['precpu_stats']['system_cpu_usage']
        cpu = container['cpu_stats']['cpu_usage']['total_usage']
        system = container['cpu_stats']['system_cpu_usage']
        cpuDelta = float(cpu) - float(previousCPU)
        systemDelta = float(system) - float(previousSystem)
        percpu_num = len(container['cpu_stats']['cpu_usage']['percpu_usage'])
        if cpuDelta > 0.0 and systemDelta > 0.0:
            container_cpu_percent = round((cpuDelta / systemDelta) * float(percpu_num) * 100.0, 2)
        else:
            container_cpu_percent = 0.00
        cpu_point = [{"measurement": 'cpu_percent', "tags": tags, "fields": {"value": float(container_cpu_percent)}}]
        points.append(cpu_point)
        # 计算内存使用率
        mem_usage = container['memory_stats']['stats']['total_rss']
        mem_limit = container['memory_stats']['limit']
        mem_percent = round(float(mem_usage) / float(mem_limit) * 100.0, 2)
        mem_total_point = [{"measurement": 'mem_total', "tags": tags, "fields": {"value": int(mem_limit)}}]
        mem_usage_point = [{"measurement": 'mem_usage', "tags": tags, "fields": {"value": int(mem_usage)}}]
        mem_percent_point = [{"measurement": 'mem_percent', "tags": tags, "fields": {"value": float(mem_percent)}}]
        points.append(mem_total_point)
        points.append(mem_usage_point)
        points.append(mem_percent_point)
        # 网络状态
        try:
            net_sent = int(container['networks']['eth0']['tx_bytes'])
            net_recv = int(container['networks']['eth0']['rx_bytes'])
        except:
            net_sent = 0
            net_recv = 0
        net_recv_point = [{"measurement": 'net_recv', "tags": tags, "fields": {"value": net_recv}}]
        net_send_point = [{"measurement": 'net_sent', "tags": tags, "fields": {"value": net_sent}}]
        points.append(net_recv_point)
        points.append(net_send_point)
        # 磁盘io状态
        block_read_data = []
        block_write_data = []
        block_read = 0
        block_write = 0
        for block in container['blkio_stats']['io_service_bytes_recursive']:
            if block['op'] == 'Read':
                block_read_data.append(int(block['value']))
            elif block['op'] == 'Write':
                block_write_data.append(int(block['value']))
            else:
                pass
        for i in block_read_data:
            block_read = int(block_read) + int(i)
        for i in block_write_data:
            block_write = int(block_write) + int(i)
        block_read_point = [{"measurement": 'io_read', "tags": tags, "fields": {"value": int(block_read)}}]
        block_write_point = [{"measurement": 'io_write', "tags": tags, "fields": {"value": int(block_write)}}]
        points.append(block_read_point)
        points.append(block_write_point)
        for point in points:
            client.write_points(point)
    except BaseException,e:
        print "docker_collector-->calculate-->%s" %e
    finally:
        return
while True:
    try:
        container_stats_list = []
        container_list = conn.containers.list()
        for obj in container_list:
            t = threading.Thread(target=get_stats, args=(obj,))
            t.setDaemon(True)
            t.start()
        for i in range(10):
            if threading.activeCount() <= 1:
                for data in container_stats_list:
                    calculate(data)
                break
            else:
                time.sleep(1)
            if i == 9:
                print "docker_collector-->theading.activecount-->%s" %threading.activeCount()
        time.sleep(sleep_time)
    except BaseException,e:
        print "docker_collector-->while True-->%s" %e