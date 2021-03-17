import docker
import os
import time

client = docker.from_env()
image = 'problemtools/icpc'
volume = {os.getcwd() + '/kattis': {'bind': '/kattis', 'mode': 'rw'}}

def verify_problem(name):
    command = 'verifyproblem /kattis/problems/' + name
    container = client.containers.run(image, command, volumes=volume, detach=True)
    time.sleep(15)
    return container.logs()

def problem_2_html(name):
    command = 'problem2html /kattis/problems/' + name
    container = client.containers.run(image, command, volumes=volume, detach=True)

print(verify_problem("hello"))