from bottle import route, run, template, request, default_app, jinja2_view
from bottle import redirect, static_file, response, debug

import os
import datetime

from uwsgidecorators import timer, mulefunc

from dockercontroller import DockerController

# Routes Below
# ===================

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='/app/static/')


@route(['/init_browser'])
def init_container():
    host = request.urlparts.scheme + '://' + request.urlparts.netloc.split(':')[0]

    client_id, queue_pos = dc.am_i_next(request.query.get('id'))

    if queue_pos < 0:
        browser = request.query.get('browser')
        url = request.query.get('url')
        ts = request.query.get('ts')
        resp = dc.do_init(browser, url, ts, host, client_id)
    else:
        resp = {'queue': queue_pos, 'id': client_id}

    response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
    return resp


@route(['/', '/index.html', '/index.htm'])
@jinja2_view('index.html', template_lookup=['templates'])
def index():
    return {}


@route(['/<path>/<ts:re:[0-9-]+>/<url:re:.*>', '/<path>/<url:re:.*>'])
@jinja2_view('replay_embed.html', template_lookup=['templates'])
def route_load_url(path='', url='', ts=''):
    browser = dc.browser_paths.get(path)

    if not browser:
        if path == 'random':
            path = dc.get_random_browser()
        else:
            path = dc.redirect_paths.get(path)

        if not path:
            path = dc.default_browser

        if ts:
            ts += '/'

        redirect('/' + path + '/' + ts + url)

    if not ts:
        ts = re.sub('[ :-]', '', str(datetime.datetime.utcnow()).split('.')[0])

    browser_info = dict(name=browser['name'],
                        os=browser['os'],
                        version=browser['version'],
                        icon=browser['icon'])

    return {'coll': path,
            'url': url,
            'ts': ts,
            'browser': browser_info,
            'static': os.environ.get('STATIC_PATH', '/static/')
           }


@route('/random')
def randompage():
    redirect(dc.get_randompage())


# Init
# ======================

dc = DockerController()

application = default_app()


def init_cleanup_timer(dc, expire_time):
    @mulefunc(1)
    def check_abandonded():
        dc.remove_expired()

    @timer(30, target='mule2')
    def check_node(signum):
        dc.check_nodes()

    check_abandonded()


init_cleanup_timer(dc, dc.REMOVE_EXP_TIME)

debug(True)

#run(host='0.0.0.0', port='9020')

