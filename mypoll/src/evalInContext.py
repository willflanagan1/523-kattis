import json
import time
from subprocess import Popen, PIPE, TimeoutExpired
from datetime import datetime
import re
import sys


def json_converter(obj):
    if isinstance(obj, datetime):
       return str(obj)


def evalInContext(code, context):
    """Use node to evaluate the javascript code"""
    start = time.time()
    input = json.dumps({"code": code, "context": context}, default=json_converter).encode("utf-8")
    try:
         proc = Popen(["node", "runner.js"], 
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
         output, error = proc.communicate(input=input, timeout=10)
         output = output.decode("utf-8")
         error  = error.decode("utf-8")
    except TimeoutExpired:
        proc.kill()
        output, error = proc.communciate(timeout=10)
        output = output.decode("utf-8")
        error  = error.decode("utf-8")
        print(f"Popen timeout: input={input}")
        print(f"               output={output}")
        print(f"               stderr={error}")
        raise
    except Exception as e:
        print(f"execInNode input={input}" + str(e))
        raise

    if error:
        print("Error while calling runner.js from EvalInContext.py\n")
        print(error)
    try:
       decoded = json.loads(output)
    except:
       print("probably have console.log statements in evalInContext.js")
       print(output)
       raise
    print("elapsed: ", time.time() - start)
    return decoded

def evalMultiple(answers, rubrics):
    """Use node to evaluate answers to multiple questions"""
    start = time.time()
    input = json.dumps({"answers": answers, "rubrics": rubrics}, default=json_converter).encode("utf-8")
    try:
         proc = Popen(["node", "static/js/runner.js"], 
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
         output, error = proc.communicate(input=input, timeout=10)
         output = output.decode("utf-8")
         error  = error.decode("utf-8")
    except TimeoutExpired:
        proc.kill()
        output, error = proc.communciate(timeout=10)
        output = output.decode("utf-8")
        error  = error.decode("utf-8")
        print(f"Popen timeout: input={input}")
        print(f"               output={output}")
        print(f"               stderr={error}")
        raise
    except Exception as e:
        print(f"execInNode input={input}" + str(e))
        raise
    if error:
        for line in error.split("\n"):
            # When doing sections where some students may not get all questions,
            # ignore the trim error message
            if (not re.match(r"error .* undefined Cannot read property 'trim' of undefined", line)
                and (len(line) > 0)):
               print(f'evalMultiple: static/js/runner.js {line}', file=sys.stderr)
        # print(error, file=sys.stderr)
    try:
        output = json.loads(output)
    except json.JSONDecodeError as err:
        print(output, file=sys.stderr)
        print(str(err), file=sys.stderr)
        output = {}
    return output


if __name__ == "__main__":
    test = evalInContext("3 * A", {"A": 4})
    print(test)
    test = evalInContext(
        "function f(A) { return len(A); }", {"_return": "f", "_args": [[1, 2, 3]]}
    )
    print(test)
