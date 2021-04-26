import docker
import os
import time

client = docker.from_env()
image = 'cstamper6/523-problem-tool'
volume = {os.getcwd() + '/COMP523/container': {'bind': '/app', 'mode': 'rw'}}

def run_submission(name):
    command = f'python3 /app/evaluator.py {name}'
    container = client.containers.run(image, command, volumes=volume, detach=True)

    # Check for logs every second for 15 seconds 
    for i in range(0, 15):
        log = container.logs()
        if log.decode("utf-8") is not '':
            # break loop if logs are returned
            break
        time.sleep(1)

    size = len(log)
    trimmedLog = log[:size - 1]

    return trimmedLog.decode("utf-8")