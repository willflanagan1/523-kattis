import docker
import os
import time

client = docker.from_env()
image = 'problemtools/icpc'
volume = {os.getcwd() + '/COMP523/kattis': {'bind': '/kattis', 'mode': 'rw'}}

def verify_problem(name):
    command = f'verifyproblem /kattis/problems/{name}'
    container = client.containers.run(image, command, volumes=volume, detach=True)
    time.sleep(15)
    return container.logs()