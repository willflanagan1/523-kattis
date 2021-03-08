'''Evaluate expressions in Python'''

import re
import json
import math
import os
import signal
from subprocess import Popen, PIPE, TimeoutExpired


def timeout_handler(num, stack):
    '''Raise an exception for equations that take too long'''
    raise Exception('timeout')

def round_to_precision(x, percision):
    y = x * (10 ** percision)
    y = math.floor(y+0.5)
    return y / (10 ** percision)

def BigOh(x):
    ''' Take absolute number, cube root, and rount to 1000 '''
    y = abs(x)
    y = y ** (1/3)
    return round_to_precision(y, 3)

def Theta(x):
    ''' Take absolute number, quad root, and rount to 1000 '''
    y = abs(x)
    y = y ** (1/4)
    return round_to_precision(y, 3)

def myLg(x):
    ''' Take absolute number, 1/5 root, and rount to 1000 '''
    y = abs(x)
    y = y ** (1/5)
    return round_to_precision(y, 3)

def recurrence(x):
    ''' Take absolute number, 1/6 root, and rount to 1000 '''
    y = abs(x)
    y = y ** (1/6)
    return round_to_precision(y, 3)

def Omega(x):
    ''' Take square, and rount to 1000 '''
    y = x ** 2
    return round_to_precision(y, 3)


def log(x):
    '''log returning ints when possible'''
    r = math.log(x)
    if int(r) == r:
        return int(r)
    return round_to_precision(r,3)

def log10(x):
    '''log10 returning ints when possible'''
    r = math.log10(x)
    if int(r) == r:
        return int(r)
    return round_to_precision(r,3)

def log2(x):
    '''log2 returning ints when possible'''
    r = math.log2(x)
    if int(r) == r:
        return int(r)
    return round_to_precision(r,3)

def sqrt(x):
    '''sqrt returning ints when possible'''
    r = math.sqrt(x)
    if int(r) == r:
        return int(r)
    return round_to_precision(r,3)


functions = {
    'BigOh': BigOh,
    'Theta': Theta,
    'lg': myLg,
    'recurrence': recurrence,
    'Omega': Omega,
    'log': log,
    'log10': math.log10,
    'log2': log2,
    'sqrt': sqrt,
    'ceiling': math.ceil,
    'floor': math.floor,
    'factorial': math.factorial,
    'abs': math.fabs
}


def evalInContext(expr, context):
    '''Evaluate an expression in the given context'''
    context = {**context, **functions}

    def lookup(m):
        '''Lookup a variable in the context'''
        v = m.group(0)
        if v in context:
            return v
        raise NameError(f'{v} is undefined')
    s = re.sub(r'\b[a-zA-Z][_a-zA-Z0-9]*', lookup, expr)
    # allow only the operators I expect
    s = re.sub(r'[^-+*/&%~<>|^a-zA-Z0-9.() \t]', "\uFFFD", s)
    prev_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1)
    try:
        value = eval(s, {}, context)
    except (SyntaxError, TypeError):
        # Entered something syntactically incorrect
        value = None
    except Exception as e:
        print('s=', s)
        print('context=', context)
        print(e)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev_handler)
    return value


if __name__ == '__main__':
    tests = [
        'A + B',
        'A * log2(B)',
        'C & D',
        'A=2',
        'Q'
    ]
    context = {'A': 2, 'B': 4, 'C': 0xf, 'D': 0xff}
    for s in tests:
        print(s, evalInContext(s, context))
