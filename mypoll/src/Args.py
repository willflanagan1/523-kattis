
# coding: utf-8

# # Args - parse arguments for CLI and Notebooks
# 
# This is my attempt at a simple argument parser for mostly key=value pairs that I can use both on the command line and in IPython notebooks. I support query parameters in notebook URLs and a _Run_ command for notebooks.
# 
# I convert this notebook to a Python script for import and use like this.
# 
# ```
# import Args
# 
# # In a notebook you need a cell boundary here so that the collection of the query string
# # can happen before the Parse. Is there a better way? The ideal would be an effectively 
# # synchronous call between python and the javascript in the front end but that seems
# # unlikely.
# 
# args = Args.Parse(
#     verbose=False,                     # optional boolean, verbose alone will set it
#     due='',                            # optional string
#     timeout=30,                        # optional int
#     limit=int,                         # required int
#     assignment=str,                    # required string
#     _config="{assignment}/config.json" # read values from a config file too.
# )
# ```
# 
# `_config` allows me to specify the path to a json configuration file to pick up values that may be overridden. The path is interpolated with all the args using the string `format` method.
# 
# The returned value is a named tuple with attributes given by the key word arguments and an attribute `extra_` that gathers other arguments.
# 
# In the shell I can run a Python script the normal with args like this:
# ```
# python3 script.py verbose limit=5 assignment=A2 rain.txt
# ```
# 
# Or I can run it as a notebook with
# ```
# jpn script verbose limit=5 assignment=A2 rain.txt
# ```
# 
# Or I can link to the notebook with
# ```
# http://localhost:8990/notebooks/script.ipynb?limit=5&assignment=A2&rain.txt
# ```
# 
# I went for this minimalist key=value format because it is simple to implement and meets my needs.

# ## Handle URL query strings
# 
# I'm injecting a bit of Javascript into the notebook so that I can grab the query string off the URL. You must put the import and the Parse call below in separate cells so that we have a chance to grab the query string off the URL.

# In[6]:

import os

# I will pack the json encoded argv into this environment variable when running with nbconvert.
evname = 'IPYTHONARGV'

# try to detect that I'm in a notebook
try:
    __IPYTHON__
except NameError:
    inIPython = False
else:
    from IPython.display import Javascript, display
    inIPython = True
    if evname not in os.environ:
        # Javascript to grab the query string
        display(Javascript('''
        require(['base/js/namespace'], function(Jupyter) {
            var ready = function() {
                var query =  window.location.search.substring(1);
                Jupyter.notebook.kernel.execute("import Args; Args._grabQS('" + query + "')");
            };
            // If the kernel is ready when we get here the event apparently doesn't fire. They should
            // use promises instead.
            if (Jupyter.notebook.kernel) {
                ready();
            } else {
                Jupyter.notebook.events.on('kernel_ready.Kernel', ready);
            }
        });
        '''))

_argv = []
def _grabQS(qs):
    '''Convert query string into an argv like list'''
    # do I need to urldecode or some such?
    global _argv
    _argv = [ kv for kv in qs.split('&') if kv ]


# ## Figure out where the args are supplied.
# 
# There are several possible sources:
# 
# 1. For notebooks running interactively I expect them in the query string as collected above.
# 2. For notebooks running from the CLI I expect them json encoded in an enviroment variable.
# 3. For normal scripts I expect them in sys.argv.

# In[ ]:

import sys
import os
import json

if not _argv:
    if evname in os.environ:
        _argv = json.loads(os.environ[evname])
    elif 'ipykernel' not in sys.argv[0]:
        _argv = sys.argv[1:]
    else:
        _argv = []


# ## Process the supplied argument definition and defaults

# In[ ]:

from collections import namedtuple
import os.path as osp

def Parse(**kwargs):
    '''Return an object containing arguments collected from an optional configuration file,
    then the values specified here, then values from the sys.argv, the URL query string, or an
    environment variable.'''
    
    args = {}
    types = {}
    extra = []
    required = set()
    supplied = set()
    
    def addValue(k, v):
        if v is None:
            if k in types and types[k] is bool:
                args[k] = True
            elif k not in types:
                extra.append(k)
            else:
                raise ValueError('{k} without value expected {t}'.format(k=k, t=types[k]))
        elif k in types:
            if types[k] is bool:
                if isinstance(v, str):
                    args[k] = v.lower() not in ['0', 'false']
                else:
                    args[k] = bool(v)
            else:
                try:
                    args[k] = types[k](v)
                except ValueError:
                    raise ValueError('{k}={v} expected {t}'.format(k=k, v=v, t=types[k]))
        else:
            raise ValueError('{k}={v} unexpected argument'.format(k=k, v=v))
        supplied.add(k)
    
    # first fill the defaults
    for k, v in kwargs.items():
        if k.startswith('_'):
            continue
        if isinstance(v, type): # a required argument
            required.add(k)
            types[k] = v
            
        else:
            args[k] = v
            types[k] = type(v)
            
    try:
        # get values from _argv
        for a in _argv:
            if '=' in a:
                k, v = a.split('=')
            else:
                k, v = a, None
            addValue(k, v)

        # get the values from the config file but don't overwrite supplied values
        if '_config' in kwargs:
            path = kwargs['_config'].format(**args)
            if osp.exists(path):
                with open(path, 'r') as fp:
                    for k, v in json.load(fp).items():
                        if k not in supplied:
                            addValue(k, v)

        # make sure we got the required values
        omitted = required - supplied
        if omitted:
            raise ValueError('missing required argument{} {}'.format('s'[len(omitted)==1:], omitted))
    except ValueError:
        # print a usage message
        print('args:', ' '.join([ '{}={}'.format(k,t.__name__) for k,t in types.items() ]))
        raise
        
    attrs = sorted(args.keys())
    attrs.append('extra_')
    args['extra_'] = extra
        
    return namedtuple('Args', attrs)(**args)


# ## Run Notebooks from the CLI
# 
# Sometimes I want to run the notebook without loading it up in the browser. `nbconvert` does nearly everything I need but it won't pass args. This is my attempt to cure that.
# 
# I'm going to allow running them two ways. 
# 
# 1. Simply convert the notebook to a python script and run it normally.
# 2. Use nbconvert to execute the notebook but arrange to pass in an environment variable with the JSON encoded argv.
# 
# I run this with a tiny script, named `jpn`, like this:
# ```
# #!/usr/bin/env python3
# import Args
# Args.Run()
# ```

# In[6]:

def Run():
    import os
    import os.path as osp
    import sys
    import subprocess
    import json
    
    name = osp.basename(sys.argv[0])
    notebook = sys.argv[1]
    
    if name == 'jpy':
        script = notebook.replace('.ipynb', '.py')
        if not osp.exists(script) or osp.getmtime(notebook) > osp.getmtime(script):
            subprocess.call(['jupyter', 'nbconvert', '--log-level', '0', '--to', 'script', notebook])
        os.execlp('ipython3', script, script, *sys.argv[2:])
        
    elif name == 'jpn':
        env = os.environ
        env['IPYTHONARGV'] = json.dumps(sys.argv[2:])
        os.execlpe('jupyter', 'jupyter', 'nbconvert', '--execute', '--ExecutePreprocessor.timeout=600', 
                   '--inplace', '--to', 'notebook', notebook, '--output', notebook, env)

