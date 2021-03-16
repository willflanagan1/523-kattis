import docker
import os

client = docker.from_env()

volume = {os.getcwd() + '/kattis': {'bind': '/kattis', 'mode': 'rw'}}

container = client.containers.run('problemtools/icpc', 'ls /kattis/problems', volumes=volume, detach=True)

print(container.logs())