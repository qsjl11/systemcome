#Deployment commands： gunicorn chatGPT_Web:app -c gunicorn_config.py

bind = '0.0.0.0:8880'    # your IP:PORT
worker_class = 'gevent'  
worker_connections = 1000
workers = 3  # Number of worker processes
timeout = 60 
loglevel = 'debug'