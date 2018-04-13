# docker-monitor
此项目提供一个完整的docker监控方案，主要包括一下内容：  
##主机监控： 
说明：通过python的psutil获取主机信息（dockerfile中修改了psutil部分内容，以获取主机信息而不是docker内部信息） 
1，程序运行在docker中监控主机状态，不需要在主机部署agent  
2，监控内容包括：主机信息、cpu、内存、网络、磁盘、io  
##docker监控：  
说明：docke监控通过docker.sock获取docker信息，每个主机只需要部署一个即可。  
1，监控指标为docker stats中的内容。  
##docker event事件监控：  
说明：通过docker的eventsapi获取docker的event信息。  
##docker logs监控：  
说明：通过读取/var/lib/docker/containers下的日志获取
  
##数据存储  
使用influxdb存储数据  
说明：采取influxdb是为了方便后续做报表，以及出现故障时，分析当时所有的指标。  
##前端展示  
使用grafana展示  
#使用方式   
##启动influxdb  
docker run -p 8086:8086 \\  
  -d \\  
  -v /usr/local/docker-monitor/monitor-data/influxdb:/var/lib/influxdb \\  
  -e INFLUXDB_HTTP_AUTH_ENABLED=true \\  
  -e INFLUXDB_DB=monitor \\  
  -e INFLUXDB_ADMIN_USER=username \\  
  -e INFLUXDB_ADMIN_PASSWORD=password \\  
  --name=influxdb \\  
  --restart always \\  
  influxdb  
##启动grafana  
docker run \\  
    -d \\  
    --name=grafana \\  
    -p 3000:3000 \\  
    -v /usr/local/docker-monitor/monitor-data/grafana:/var/lib/grafana \\  
    --restart always \\  
    grafana/grafana
##启动docker-monitor(在被监控服务器上)  
1，修改config.json文件  
2，通过Dockerfile生成镜像  
3，在被监控机器上启动镜像  
docker run -d \\  
    --name docker-monitor \\  
    -v /var/run/docker.sock:/var/run/docker.sock \\  
    -v /proc:/host_proc \\  
    -v /sys:/host_sys \\  
    -v /var/lib/docker/containers:/var/lib/docker/containers \\  
    --restart always \\  
    docker-monitor:v1  
##后续  
后续根据个人需求，在grafana上配置influxdb连接，添加图表