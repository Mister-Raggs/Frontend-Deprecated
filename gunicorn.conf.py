# -*- encoding: utf-8 -*-

bind = "0.0.0.0:8080"
workers = 3
worker_connections = 300
accesslog = "./logs/gunicorn-access.log"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = False
