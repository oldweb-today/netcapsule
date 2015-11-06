from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view, static_file

import os
import base64
import datetime
import time
import re
import atexit
import redis
import yaml
import json

from uwsgidecorators import timer
import uwsgi

MAX_CONT = 100

#=============================================================================
class DockerController(object):
    def _load_config(self):
        with open('./config.yaml') as fh:
            config = yaml.load(fh)
        return config

    def __init__(self):
        config = self._load_config()

        self.LOCAL_REDIS_HOST = 'netcapsule_redis_1'
        self.REDIS_HOST = os.environ.get('REDIS_HOST', self.LOCAL_REDIS_HOST)
        self.PYWB_HOST = os.environ.get('PYWB_HOST', 'netcapsule_pywb_1')
        self.C_EXPIRE_TIME = config['container_expire_secs']
        self.Q_EXPIRE_TIME = config['queue_expire_secs']
        self.REMOVE_EXP_TIME = config['remove_expired_secs']
        self.VERSION = config['api_version']

        self.VNC_PORT = config['vnc_port']
        self.CMD_PORT = config['cmd_port']

        self.image_prefix = config['image_prefix']
        self.browsers = config['browsers']

        self.redis = redis.StrictRedis(host=self.REDIS_HOST)

        self.redis.setnx('next_client', '1')

        if os.path.exists('/var/run/docker.sock'):
            self.cli = Client(base_url='unix://var/run/docker.sock',
                              version=self.VERSION)
        else:
            kwargs = kwargs_from_env(assert_hostname=False)
            kwargs['version'] = self.VERSION
            self.cli = Client(**kwargs)

    def _get_host_port(self, info, port, default_host):
        info = info['NetworkSettings']['Ports'][str(port) + '/tcp']
        info = info[0]
        host = info['HostIp']
        if host == '0.0.0.0' and default_host:
            host = default_host

        return host + ':' + info['HostPort']

    def new_container(self, browser, env=None, default_host=None):
        tag = self.browsers.get(browser)

        # get default browser
        if not tag:
            tag = self.browsers['']

        container = self.cli.create_container(image=self.image_prefix + '/' + tag,
                                              ports=[self.VNC_PORT, self.CMD_PORT],
                                              environment=env,
                                             )
        id_ = container.get('Id')

        res = self.cli.start(container=id_,
                             port_bindings={self.VNC_PORT: None, self.CMD_PORT: None},
                             volumes_from=['netcapsule_shared_data_1'],
                            )

        self.cli.connect_container_to_network(id_, 'netcapsule')

        info = self.cli.inspect_container(id_)
        ip = info['NetworkSettings']['IPAddress']

        short_id = id_[:12]
        self.redis.hset('all_containers', short_id, ip)
        self.redis.setex('c:' + short_id, self.C_EXPIRE_TIME, 1)

        return {'vnc_host': self._get_host_port(info, self.VNC_PORT, default_host),
                'cmd_host': self._get_host_port(info, self.CMD_PORT, default_host)}

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

    def add_new_client(self):
        client_id = self.redis.incr('clients')
        enc_id = base64.b64encode(os.urandom(27))
        self.redis.setex('cm:' + enc_id, self.Q_EXPIRE_TIME, client_id)
        self.redis.setex('q:' + str(client_id), self.Q_EXPIRE_TIME, 1)
        return enc_id, client_id

    def am_i_next(self, enc_id):
        client_id = None
        if enc_id:
            self.redis.expire('cm:' + enc_id, self.Q_EXPIRE_TIME)
            client_id = self.redis.get('cm:' + enc_id)

        if not client_id:
            enc_id, client_id = dc.add_new_client()

        client_id = int(client_id)
        next_client = int(self.redis.get('next_client'))

        # not next client
        if next_client != client_id:
            # if this client expired, delete it from queue
            if not self.redis.get('q:' + str(next_client)):
                print('skipping expired', next_client)
                self.redis.incr('next_client')

            # missed your number somehow, get a new one!
            if client_id < next_client:
                enc_id, client_id = self.add_new_client()
            else:
                self.redis.expire('q:' + str(client_id), self.Q_EXPIRE_TIME)

            return enc_id, client_id - next_client

        # not avail yet
        num_containers = self.redis.hlen('all_containers')
        if num_containers >= MAX_CONT:
            self.redis.expire('q:' + str(client_id), self.Q_EXPIRE_TIME)
            return enc_id, client_id - next_client

        self.redis.incr('next_client')
        return enc_id, -1


@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='/app/static/')


@route(['/init_browser'])
def init_container():
    host = request.environ.get('HTTP_HOST', '')
    host = host.split(':')[0]

    client_id, queue_pos = dc.am_i_next(request.query.get('id'))

    if queue_pos < 0:
        browser = request.query.get('browser')
        url = request.query.get('url')
        ts = request.query.get('ts')
        resp = do_init(browser, url, ts, host)
    else:
        resp = {'queue': queue_pos, 'id': client_id}

    return resp


def do_init(browser, url, ts, host):
    env = {}
    env['URL'] = url
    env['TS'] = ts
    env['SCREEN_WIDTH'] = os.environ.get('SCREEN_WIDTH')
    env['SCREEN_HEIGHT'] = os.environ.get('SCREEN_HEIGHT')
    env['REDIS_HOST'] = dc.REDIS_HOST
    env['PYWB_HOST_PORT'] = dc.PYWB_HOST + ':8080'

    info = dc.new_container(browser, env, host)
    info['queue'] = 0
    return info

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

