from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view, static_file

import os
import datetime
import time
import re
import atexit
import redis

from uwsgidecorators import timer
import uwsgi


VNC_PORT = 6080
CMD_PORT = 6082
VERSION='1.18'
PYWB_HOST = 'netcapsule_pywb_1'
REDIS_HOST = 'netcapsule_redis_1'

EXPIRE_TIME = 120
CHECK_TIME = 10


#=============================================================================
class DockerController(object):
    def __init__(self):
        self.redis = redis.StrictRedis(host=REDIS_HOST)

        if os.path.exists('/var/run/docker.sock'):
            self.cli = Client(base_url='unix://var/run/docker.sock',
                              version=VERSION)
        else:
            kwargs = kwargs_from_env()
            kwargs['tls'].assert_hostname = False
            kwargs['version'] = VERSION
            self.cli = Client(**kwargs)

    def new_container(self, tag, env=None):
        container = self.cli.create_container(image=tag,
                                              ports=[VNC_PORT, CMD_PORT],
                                              environment=env)
        id_ = container.get('Id')

        res = self.cli.start(container=id_,
                             port_bindings={VNC_PORT: None, CMD_PORT: None},
                             links={PYWB_HOST: PYWB_HOST,
                                    REDIS_HOST: REDIS_HOST})

        vnc_port = self.cli.port(id_, VNC_PORT)
        vnc_port = vnc_port[0]['HostPort']

        cmd_port = self.cli.port(id_, CMD_PORT)
        cmd_port = cmd_port[0]['HostPort']

        info = self.cli.inspect_container(id_)
        ip = info['NetworkSettings']['IPAddress']

        short_id = id_[:12]
        self.redis.hset('all_containers', short_id, ip)
        self.redis.setex('c:' + short_id, EXPIRE_TIME, 1)

        return vnc_port, cmd_port

    def remove_container(self, short_id, ip):
        print('REMOVING ' + short_id)
        try:
            self.cli.remove_container(short_id, force=True)
        except Exception as e:
            print(e)

        self.redis.hdel('all_containers', short_id)
        self.redis.delete('c:' + short_id)

        ip_keys = self.redis.keys(ip +':*')
        for key in ip_keys:
            self.redis.delete(key)

    def remove_all(self, check_expired=False):
        all_containers = self.redis.hgetall('all_containers')

        for short_id, ip in all_containers.iteritems():
            if check_expired:
                remove = not self.redis.get('c:' + short_id)
            else:
                remove = True

            if remove:
                self.remove_container(short_id, ip)


@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='/app/static/')


@route(['/init_browser'])
def init_container():
    browser = request.query.get('browser')
    url = request.query.get('url')
    ts = request.query.get('ts')

    if browser == 'ns' or browser == 'netscape':
        tag = 'netcapsule/netscape'
    elif browser == 'mosaic':
        tag = 'netcapsule/mosaic'
    elif browser == 'ie4':
        tag = 'netcapsule/ie4'
    elif browser == 'ie5' or browser == 'ie55':
        tag = 'netcapsule/ie5.5'
    elif browser == 'firefox':
        tag = 'netcapsule/firefox'
    else:
        tag = 'netcapsule/firefox'

    vnc_port, cmd_port = dc.new_container(tag, {'URL': url, 'TS': ts})

    host = request.environ.get('HTTP_HOST')
    host = host.split(':')[0]

    vnc_host = host + ':' + vnc_port
    cmd_host = host + ':' + cmd_port

    return {'vnc_host': vnc_host,
            'cmd_host': cmd_host
           }


@route(['/<path>/<ts:re:[0-9-]+>/<url:re:.*>', '/<path>/<url:re:.*>'])
@jinja2_view('replay.html', template_lookup=['templates'])
def route_load_url(path='', url='', ts=''):
    if not ts:
        ts = re.sub('[ :-]', '', str(datetime.datetime.utcnow()).split('.')[0])

    return {'coll': path,
            'url': url,
            'ts': ts}


def onexit():
    dc.remove_all(False)

dc = DockerController()

application = default_app()

@timer(CHECK_TIME, target='mule')
def check_abandonded(signum):
    #while True:
    dc.remove_all(True)


uwsgi.atexit = onexit

#run(host='0.0.0.0', port='9020')

