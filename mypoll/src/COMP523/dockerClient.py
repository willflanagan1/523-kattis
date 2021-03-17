import docker
import os
import time

client = docker.from_env()

volume = {os.getcwd() + '/kattis': {'bind': '/kattis', 'mode': 'rw'}}

container = client.containers.run('problemtools/icpc', 'verifyproblem /kattis/problems/guess', volumes=volume, detach=True)

while True:
    time.sleep(25)
    print(container.logs())