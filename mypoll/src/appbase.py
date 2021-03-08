"""Basics of a Bottle web server

Gary Bishop May 2020
"""

import bottle
import getpass
import json
import os.path as osp
import sys
from config import admins


# lax security when testing
Testing = False

# startup bottle
app = application = bottle.Bottle()

def log(*args):
   """Print for debugging especially when doing make deploy"""
   print(*args, file=sys.stderr)

# make get_url available in all templates
def get_url(name, user=None, **kwargs):
    """get_url for use from templates"""
    url = app.get_url(name, **kwargs)
    real_user = get_user()
    if user and user_is_admin(real_user) and real_user != user:
        url = url + f"?user={user}"
    return url

# make anchor for itinerary
def itinerary_anchor(content, href):
    return f"<a href='{href}'><nobr>{content}</nobr></a>"


bottle.SimpleTemplate.defaults["get_url"] = get_url


# load secrets needed at runtime
secrets = json.load(open("secrets.json", "r"))


def allow_json(func):
    """ Decorator: renders as json if requested """

    def wrapper(*args, **kwargs):
        """wrapper"""
        result = func(*args, **kwargs)
        if "application/json" in bottle.request.headers.get(
            "Accept", ""
        ) and isinstance(result, dict):
            return bottle.HTTPResponse(result)
        return result

    return wrapper


# simple minded security
def user_is_known(username, _password=None):
    """The user has logged in"""
    return username


def user_is_admin(username, _password=None):
    """The user is an administrator"""
    return username in admins


def get_user():
    """Return the user from the cookie"""
    user = bottle.request.get_cookie("user", secret=secrets["cookie"])
    return user


bottle.SimpleTemplate.defaults["get_user"] = get_user
bottle.SimpleTemplate.defaults["user_is_admin"] = user_is_admin


def set_user(user):
    """Set the user in the cookie"""
    bottle.response.set_cookie(
        "user", user, secret=secrets["cookie"], secure=not Testing
    )


def auth(check, fail=False):
    """decorator to apply above functions for auth"""

    def decorator(function):
        """decorate itself"""

        def wrapper(*args, **kwargs):
            """wrapper"""
            user = get_user()
            if not user and fail:
                log(f'auth: user {user} fail {fail}')
                raise bottle.HTTPError(403, "Forbidden")
            elif not user:
                path = bottle.request.path[1:]
                bottle.redirect(app.get_url("login") + "?path=" + path)
            elif not check(user):
                log(f'auth: user {user} check {check} check(user) {check(user)}')
                raise bottle.HTTPError(403, "Forbidden")
            return function(*args, **kwargs)

        return wrapper

    return decorator


def static(filename):
    """
    Produce the path to a static file
    """
    p = osp.join("./static", filename)
    m = osp.getmtime(p)
    s = "%x" % int(m)
    u = app.get_url("static", filename=filename)
    return u + "?" + s


bottle.SimpleTemplate.defaults["static"] = static


@app.route("/static/<filename:path>", name="static")
def serveStatic(filename):
    """
    Serve static files in development
    """
    kwargs = {"root": "./static"}
    if filename.endswith(".sqlite"):
        kwargs["mimetype"] = "application/octet-stream"
    # fake up errors for testing
    # import random
    # if random.random() < 0.5:
    #     return bottle.HTTPError(404, 'bogus')
    return bottle.static_file(filename, **kwargs)


@app.route("/login", name="login")
@bottle.view("login")
def login():
    """handle login with basic auth"""
    path = bottle.request.query.path
    return {"path": path, "message": ""}


@app.post("/login")
@bottle.view("login")
def loginpost():
    """handle login submit"""
    forms = bottle.request.forms
    user = forms.user
    passwd = forms.passwd
    path = forms.path
    if Testing:
        ok = user in admins
    else:
        import pam

        p = pam.pam()
        ok = p.authenticate(user, passwd, "nginx")
    if not ok:
        return {"path": path, "message": "login failed"}
    set_user(user)
    if path:
        bottle.redirect(app.get_url("root") + path)
    else:
        bottle.redirect(app.get_url("root"))


@app.route("/logout", name="logout")
def logout():
    """Allow user to log out"""
    bottle.response.set_cookie("user", "", secrets["cookie"])
    bottle.redirect(app.get_url("login"))


@app.route("/api/user")
@app.route("/user")
@auth(user_is_known)
def user():
    """Report the current user for display on the page"""
    return {"user": get_user()}


@app.error(404)
def error404(error):
    """Return a custom 404 message"""
    user = get_user()
    msg = f"""Sorry {user}: File not found. Every access is recorded."""
    return msg


class StripPathMiddleware:
    """
    Get that slash out of the request
    """

    def __init__(self, a):
        self.a = a

    def __call__(self, e, h):
        e["PATH_INFO"] = e["PATH_INFO"].rstrip("/")
        return self.a(e, h)


def serve(test=True):
    """Run the server for testing"""
    from livereload import Server

    global Testing
    Testing = test

    bottle.debug(True)
    server = Server(StripPathMiddleware(app))
    if getpass.getuser() == 'jmajikes':
       port = '8081'
    elif getpass.getuser() == 'isabelz':
       port = '8080'
    elif getpass.getuser() == 'sharma':
       port = '8082'
    elif getpass.getuser() == 'haidyi':
       port = '8083'
    elif getpass.getuser() == 'mapy':
       port = '8084'
    elif getpass.getuser() == 'ycshen':
       port = '8085'
    elif getpass.getuser() == 'kaihao':
       port = '8086'
    elif getpass.getuser() == 'terrell':
       port = '8088'
    elif getpass.getuser() == 'willflan':
       port = '8091'
    else:
       port = '8087'
    server.serve(port=port, host="0.0.0.0", restart_delay=2)
