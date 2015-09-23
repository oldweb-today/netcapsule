from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view, static_file

import os
import datetime
import time
import re
import atexit
import redis
import yaml

from uwsgidecorators import timer
import uwsgi


#=============================================================================
class DockerController(object):
    def _load_config(self):
        with open('./config.yaml') as fh:
            config = yaml.load(fh)
        return config

    def __init__(self):
        config = self._load_config()

        self.REDIS_HOST = config['redis_host']
        self.PYWB_HOST = config['pywb_host']
        self.EXPIRE_TIME = config['expire_secs']
        self.REMOVE_EXP_TIME = config['remove_expired_secs']
        self.VERSION = config['api_version']

        self.VNC_PORT = config['vnc_port']
        self.CMD_PORT = config['cmd_port']

        self.image_prefix = config['image_prefix']
        self.browsers = config['browsers']

        self.redis = redis.StrictRedis(host=self.REDIS_HOST)

        if os.path.exists('/var/run/docker.sock'):
            self.cli = Client(base_url='unix://var/run/docker.sock',
                              version=self.VERSION)
        else:
            kwargs = kwargs_from_env()
            kwargs['tls'].assert_hostname = False
            kwargs['version'] = self.VERSION
            self.cli = Client(**kwargs)

    def new_container(self, browser, env=None):
        tag = self.browsers.get(browser)

        # get default browser
        if not tag:
            tag = self.browsers['']

        container = self.cli.create_container(image=self.image_prefix + '/' + tag,
                                              ports=[self.VNC_PORT, self.CMD_PORT],
                                              environment=env)
        id_ = container.get('Id')

        res = self.cli.start(container=id_,
                             port_bindings={self.VNC_PORT: None, self.CMD_PORT: None},
                             links={self.PYWB_HOST: self.PYWB_HOST,
                                    self.REDIS_HOST: self.REDIS_HOST})

        vnc_port = self.cli.port(id_, self.VNC_PORT)
        vnc_port = vnc_port[0]['HostPort']

        cmd_port = self.cli.port(id_, self.CMD_PORT)
        cmd_port = cmd_port[0]['HostPort']

        info = self.cli.inspect_container(id_)
        ip = info['NetworkSettings']['IPAddress']

        short_id = id_[:12]
        self.redis.hset('all_containers', short_id, ip)
        self.redis.setex('c:' + short_id, self.EXPIRE_TIME, 1)

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

    env = {}
    env['URL'] = url
    env['TS'] = ts
    env['SCREEN_WIDTH'] = os.environ.get('SCREEN_WIDTH')
    env['SCREEN_HEIGHT'] = os.environ.get('SCREEN_HEIGHT')

    vnc_port, cmd_port = dc.new_container(browser, env)

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

uwsgi.atexit = onexit

def init_cleanup_timer(dc, expire_time):
    @timer(expire_time, target='mule')
    def check_abandonded(signum):
        dc.remove_all(True)

init_cleanup_timer(dc, dc.REMOVE_EXP_TIME)

#run(host='0.0.0.0', port='9020')

