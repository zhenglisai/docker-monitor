#!/usr/bin/env python
# -*- coding:utf-8 -*-
import psutil
import os
import json
import docker
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
sleep_time = config['sleep_time']
eth_name = config['eth_name']
while True:
    try:
        docker_info = conn.info()
        tags = {'type':'host'}
        points = []
        ###host_info###
        tags['name'] = docker_info['Name']
        try:
            tags['ip'] = psutil.net_if_addrs()[eth_name][0][1]
        except:
            tags['ip'] = "NULL"
        boot_time_point = [{"measurement": 'boot_time', "tags": tags, "fields": {"value": int(psutil.boot_time())}}]
        points.append(boot_time_point)
        ###host_cput###
        cpu_percent_point = [{"measurement": 'cpu_percent', "tags": tags, "fields": {"value": float(psutil.cpu_percent())}}]
        points.append(cpu_percent_point)
        cpu_load_5_point = [{"measurement": 'cpu_load_5', "tags": tags, "fields": {"value": float(os.getloadavg()[1])}}]
        points.append(cpu_load_5_point)
        cpu_load_15_point = [{"measurement": 'cpu_load_15', "tags": tags, "fields": {"value": float(os.getloadavg()[2])}}]
        points.append(cpu_load_15_point)
        cpu_times_percent = psutil.cpu_times_percent()
        for name in cpu_times_percent._fields:
            cpu_times_point = [{"measurement": 'cpu_percent_%s' %name, "tags": tags, "fields": {"value": float(cpu_times_percent.__getattribute__(name))}}]
            points.append(cpu_times_point)
        ###host_mem###
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        mem_total_point = [{"measurement": 'mem_total', "tags": tags, "fields": {"value": int(mem.total)}}]
        mem_usage = mem.total - mem.available
        mem_usage_point = [{"measurement": 'mem_usage', "tags": tags, "fields": {"value": int(mem_usage)}}]
        mem_percent_point = [{"measurement": 'mem_percent', "tags": tags, "fields": {"value": float(mem.percent)}}]
        mem_swap_total_point = [{"measurement": 'mem_swap_total', "tags": tags, "fields": {"value": int(swap.total)}}]
        mem_swap_usage_point = [{"measurement": 'mem_swap_usage', "tags": tags, "fields": {"value": int(swap.used)}}]
        mem_swap_percent_point = [{"measurement": 'mem_swap_percent', "tags": tags, "fields": {"value": float(swap.percent)}}]
        points.append(mem_total_point)
        points.append(mem_usage_point)
        points.append(mem_percent_point)
        points.append(mem_swap_total_point)
        points.append(mem_swap_usage_point)
        points.append(mem_swap_percent_point)
        ####disk####
        disk_partitions = psutil.disk_partitions()
        for i in disk_partitions:
            mount_point = i.mountpoint
            mount_point_info = psutil.disk_usage(mount_point)
            mount_total_point = [{"measurement": 'disk_host_total_%s' %mount_point, "tags": tags, "fields": {"value": int(mount_point_info.total)}}]
            mount_used_point = [{"measurement": 'disk_host_usage_%s' % mount_point, "tags": tags,"fields": {"value": int(mount_point_info.used)}}]
            mount_percent_point = [{"measurement": 'disk_host_percent_%s' % mount_point, "tags": tags,"fields": {"value": float(mount_point_info.percent)}}]
            points.append(mount_total_point)
            points.append(mount_used_point)
            points.append(mount_percent_point)
        ####docker disk####
        running_containers_point = [{"measurement": 'containers_running', "tags": tags,"fields": {"value": int(docker_info['ContainersRunning'])}}]
        stopped_containers_point = [{"measurement": 'containers_stopped', "tags": tags, "fields": {"value": int(docker_info['ContainersStopped'])}}]
        paused_containers_point = [{"measurement": 'containers_paused', "tags": tags, "fields": {"value": int(docker_info['ContainersPaused'])}}]
        points.append(running_containers_point)
        points.append(stopped_containers_point)
        points.append(paused_containers_point)
        driver_type = docker_info['Driver']
        if driver_type == 'devicemapper':
            driver_status = docker_info['DriverStatus']
            for driver in driver_status:
                if driver[0] == 'Data Space Total':
                    disk_total_data = driver[1]
                    if disk_total_data[-2] == "G":
                        disk_total = round(float(disk_total_data[:-2]) * 1000, 2)
                    elif disk_total_data[-2] == "M":
                        disk_total = round(float(disk_total_data[:-2]),2)
                    elif disk_total_data[-2] == "k":
                        disk_total = round(float(disk_total_data[:-2]) / 1000, 2)
                    else:
                        disk_total = round(float(disk_total_data[:-2]) / 1000000, 2)
                    disk_total_point = [{"measurement": 'disk_docker_total', "tags": tags, "fields": {"value": float(disk_total)}}]
                    points.append(disk_total_point)
                elif driver[0] == 'Data Space Used':
                    disk_used_data = driver[1]
                    if disk_used_data[-2] == 'G':
                        disk_used = round(float(disk_used_data[:-2]) * 1000, 2)
                    elif disk_used_data[-2] == 'M':
                        disk_used = round(float(disk_used_data[:-2]), 2)
                    elif disk_used_data[-2] == 'k':
                        disk_used = round(float(disk_used_data[:-2]) / 1000, 2)
                    else:
                        disk_used = round(float(disk_used_data[:-2]) / 1000000, 2)
                    disk_used_point = [{"measurement": 'disk_docker_used', "tags": tags, "fields": {"value": float(disk_used)}}]
                    points.append(disk_used_point)
                else:
                    pass
        else:
            pass
        ###io###
        io_info = psutil.disk_io_counters()
        io_read_count_point = [{"measurement": 'io_read_count', "tags": tags, "fields": {"value": int(io_info.read_count)}}]
        io_write_count_point = [{"measurement": 'io_write_count', "tags": tags, "fields": {"value": int(io_info.write_count)}}]
        io_read_bytes_point = [{"measurement": 'io_read_bytes', "tags": tags, "fields": {"value": int(io_info.read_bytes)}}]
        io_write_bytes_point = [{"measurement": 'io_write_bytes', "tags": tags, "fields": {"value": int(io_info.read_bytes)}}]
        io_read_time_point = [{"measurement": 'io_read_time', "tags": tags, "fields": {"value": int(io_info.read_time)}}]
        io_write_time_point = [{"measurement": 'io_read_time', "tags": tags, "fields": {"value": int(io_info.write_time)}}]
        points.append(io_read_bytes_point)
        points.append(io_write_bytes_point)
        points.append(io_read_count_point)
        points.append(io_write_count_point)
        points.append(io_read_time_point)
        points.append(io_write_time_point)
        ###net###
        net_io_info = psutil.net_io_counters()
        net_connections = psutil.net_connections(kind='tcp4')
        net_sent_point = [{"measurement": 'net_sent', "tags": tags, "fields": {"value": int(net_io_info.bytes_sent)}}]
        net_recv_point = [{"measurement": 'net_recv', "tags": tags, "fields": {"value": int(net_io_info.bytes_recv)}}]
        points.append(net_sent_point)
        points.append(net_recv_point)
        net_status = {}
        for net in net_connections:
            if net_status.has_key(net.status):
                net_status[net.status] += 1
            else:
                net_status[net.status] = 1
        for key in net_status:
            key_point = [{"measurement": 'net_status_%s' %key, "tags": tags, "fields": {"value": int(net_status[key])}}]
            points.append(key_point)
        ###write data into influxdb####
        for point in points:
            client.write_points(point)
    except BaseException,e:
        print "host_collector.py-->while True-->%s" %e
    time.sleep(sleep_time)