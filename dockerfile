FROM python:2.7.14-alpine3.7
RUN apk update && apk add --no-cache gcc python-dev musl-dev linux-headers && pip install --no-cache-dir docker psutil influxdb
RUN sed -i 's/\/proc/\/host_proc/g' /usr/local/lib/python2.7/site-packages/psutil/__init__.py && sed -i 's/\/proc/\/host_proc/g' /usr/local/lib/python2.7/site-packages/psutil/_pslinux.py && sed -i 's/\/sys/\/host_sys/g' /usr/local/lib/python2.7/site-packages/psutil/_pslinux.py
WORKDIR /monitor
COPY ./* ./
CMD ["sh","start.sh"]