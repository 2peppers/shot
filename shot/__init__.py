from functools import wraps
import sys
import datetime
import re
import sys
import os
import traceback
from ast import literal_eval as eval
from collections import OrderedDict as odict
from operator import eq, gt, lt, contains

from shot.exc import RouteNotFound, TemplateSyntaxError
from shot.templater import Templater

HEADERS = [
    ('Content-Type', 'text/html'),
    #('Server', str(sys.version.split(maxsplit=1)[0]))
]
settings = dict(
    DEBUG=True,
    ENCODING='utf-8', 
    TEMPLATES_DIR='templates',
    BASE_DIR=os.getcwd())
ASSETS_DIR = os.path.dirname(__file__) + '/assets/'
APP_ROUTES = {}
ROUTES_TO_ADD = []

def route(url='', status_code="200 OK"):
    def deco(view_function):
        view_function.url = url
        view_function.status_code = status_code
        APP_ROUTES[url] = (status_code, view_function)
        return view_function
    return deco

def render(template, context=None):
    'Simple wrapper for Templater'
    return Templater(template, context).render()

def process_routes():
    APP_ROUTES.update({ obj.url: (obj.status_code, obj) \
                      for obj in globals().values() \
                        if callable(obj) and hasattr(obj, "url")})

def application(environ, start_response):
    headers = HEADERS #+ \
        #[('Date', datetime.datetime.utcnow().strftime("%a, %d %b %Y %X"))]
    process_routes()
    try:
        status_code, view_function = APP_ROUTES[environ['PATH_INFO']]
    except KeyError:
        start_response("404 Page not found", headers)
        return [render(ASSETS_DIR + '404.html', {'route': environ['PATH_INFO'], 'routes': APP_ROUTES if settings['DEBUG'] else None})]
    start_response(status_code, headers)
    try:
        data = view_function(environ)
        if isinstance(data, str):
            return [data.encode(settings.get('ENCODING', 'utf-8'))]
        return [data]
    except RouteNotFound as err:
        return [render(ASSETS_DIR + '404.html', {'message': err.msg, 'routes': APP_ROUTES if settings['DEBUG'] else None})]
    except TemplateSyntaxError as err:
        if settings['DEBUG']:
            return [render(ASSETS_DIR +'exc.html', {'err': err, 'url': environ['PATH_INFO'], 'view': view_function.__name__})]
        else:
            return [render(ASSETS_DIR +'500.html')]
    except Exception as err:
        if settings['DEBUG']:
            trace_as_html = traceback.format_exc().replace("\n", '<br/>')
            debug_context = {'err': err, 'traceback': trace_as_html, 'url': environ['PATH_INFO'], 'view': view_function.__name__}
            return [render(ASSETS_DIR + '500.html', debug_context)]
        else:
            return [render(ASSETS_DIR + '500.html', {'err': err})]