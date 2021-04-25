import docker
import os
import time

client = docker.from_env()
image = 'cstamper6/523-problem-tool'
volume = {os.getcwd() + '/COMP523/container': {'bind': '/app', 'mode': 'rw'}}

def run_submission(name):
    command = f'python3 /app/evaluator.py {name}'
    container = client.containers.run(image, command, volumes=volume, detach=True)

    time.sleep(15)

    # trim logs to match format
    log = container.logs()
    size = len(log)
    trimmedLog = log[:size - 1]

    return trimmedLog.decode("utf-8")