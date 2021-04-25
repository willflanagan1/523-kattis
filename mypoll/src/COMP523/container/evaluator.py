import sys
import os
from subprocess import check_output

sampleInput = open('app/submissions/sampleInput.txt').read()

fileName = sys.argv[1]

if (len(sampleInput) != 0):
    print(check_output([sys.executable, f'app/submissions/{fileName}'],
        input=sampleInput,
        universal_newlines=True))
else:
    print(check_output([sys.executable, f'app/submissions/{fileName}'],
        universal_newlines=True))