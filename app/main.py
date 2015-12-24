from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view
from bottle import redirect, static_file, response

import os
import base64
import datetime
import time
import re
import atexit
import redis
import yaml
import json
import random
import itertools
import traceback

from uwsgidecorators import timer, mulefunc
import uwsgi


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
        self.C_EXPIRE_TIME = config['init_container_expire_secs']
        self.Q_EXPIRE_TIME = config['queue_expire_secs']
        self.REMOVE_EXP_TIME = config['remove_expired_secs']
        self.VERSION = config['api_version']

        self.VNC_PORT = config['vnc_port']
        self.CMD_PORT = config['cmd_port']

        self.MAX_CONT = config['max_containers']

        self.image_prefix = config['image_prefix']

        self.browser_list = config['browsers']
        self.browser_paths = {}

        for browser in self.browser_list:
            path = browser['path']
            if path in self.browser_paths:
                raise Exception('Already a browser for path {0}'.format(path))

            self.browser_paths[path] = browser

        self.default_browser = config['default_browser']
        self.redirect_paths = config['redirect_paths']

        self.randompages = []
        try:
            with open(config['random_page_file']) as fh:
                self.randompages = list([line.rstrip() for line in fh])
        except Exception as e:
            print(e)

        self.redis = redis.StrictRedis(host=self.REDIS_HOST)

        self.redis.setnx('next_client', '1')
        self.redis.setnx('max_containers', self.MAX_CONT)
        self.redis.setnx('num_containers', '0')
        self.redis.setnx('cpu_auto_adjust', 5.5)

        throttle_samples = config['throttle_samples']
        self.redis.setnx('throttle_samples', throttle_samples)

        throttle_max_avg = config['throttle_max_avg']
        self.redis.setnx('throttle_max_avg', throttle_max_avg)

        self.redis.setnx('container_expire_secs',
                         config['full_container_expire_secs'])

        self.T_EXPIRE_TIME = config['throttle_expire_secs']

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

    def timed_new_container(self, browser, env, host, client_id):
        start = time.time()
        info = self.new_container(browser, env, host)
        end = time.time()
        dur = end - start

        time_key = 't:' + client_id
        self.redis.setex(time_key, self.T_EXPIRE_TIME, dur)

        throttle_samples = int(self.redis.get('throttle_samples'))
        print('INIT DUR: ' + str(dur))
        self.redis.lpush('init_timings', time_key)
        self.redis.ltrim('init_timings', 0, throttle_samples - 1)

        return info

    def new_container(self, browser_id, env=None, default_host=None):
        browser = self.browser_paths.get(browser_id)

        # get default browser
        if not browser:
            browser = self.browser_paths.get(self.default_browser)

        if browser.get('req_width'):
            env['SCREEN_WIDTH'] = browser.get('req_width')

        if browser.get('req_height'):
            env['SCREEN_HEIGHT'] = browser.get('req_height')

        container = self.cli.create_container(image=self.image_prefix + '/' + browser['id'],
                                              ports=[self.VNC_PORT, self.CMD_PORT],
                                              environment=env,
                                             )
        short_id = None
        try:
            id_ = container.get('Id')
            short_id = id_[:12]

            res = self.cli.start(container=id_,
                                 port_bindings={self.VNC_PORT: None, self.CMD_PORT: None},
                                 volumes_from=['netcapsule_shared_data_1'],
                                 network_mode='netcapsule',
                                )

            info = self.cli.inspect_container(id_)
            ip = info['NetworkSettings']['IPAddress']
            if not ip:
                ip = info['NetworkSettings']['Networks']['netcapsule']['IPAddress']

            #self.redis.hset('all_containers', short_id, ip)
            self.redis.incr('num_containers')
            self.redis.setex('c:' + short_id, self.C_EXPIRE_TIME, 1)

            return {'vnc_host': self._get_host_port(info, self.VNC_PORT, default_host),
                    'cmd_host': self._get_host_port(info, self.CMD_PORT, default_host),
                   }
        except Exception as e:
            if short_id:
                self.remove_container(short_id)

            traceback.print_exc(e)
            return {}

    def remove_container(self, short_id, ip=None):
        print('REMOVING ' + short_id)
        try:
            self.cli.remove_container(short_id, force=True)
        except Exception as e:
            print(e)

        #self.redis.hdel('all_containers', short_id)
        self.redis.delete('c:' + short_id)

        if ip:
            ip_keys = self.redis.keys(ip + ':*')
            for key in ip_keys:
                self.redis.delete(key)

    def remove_expired(self):
        print('Start Expired Check')
        while True:
            try:
                value = self.redis.blpop('remove_q', 1000)
                if not value:
                    continue

                short_id, ip = value[1].split(' ')
                self.remove_container(short_id, ip)
                self.redis.decr('num_containers')
            except Exception as e:
                traceback.print_exc(e)

    def check_nodes(self):
        print('Check Nodes')
        try:
            scale = self.redis.get('cpu_auto_adjust')
            if not scale:
                return

            info = self.cli.info()
            cpus = int(info.get('NCPU', 0))
            if cpus <= 1:
                return

            total = int(float(scale) * cpus)
            self.redis.set('max_containers', total)

        except Exception as e:
            print(e)


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
            enc_id, client_id = self.add_new_client()

        client_id = int(client_id)
        next_client = int(self.redis.get('next_client'))

        # not next client
        if client_id != next_client:
            # if this client expired, delete it from queue
            if not self.redis.get('q:' + str(next_client)):
                print('skipping expired', next_client)
                self.redis.incr('next_client')

            # missed your number somehow, get a new one!
            if client_id < next_client:
                enc_id, client_id = self.add_new_client()

        diff = client_id - next_client

        if self.throttle():
            self.redis.expire('q:' + str(client_id), self.Q_EXPIRE_TIME)
            return enc_id, client_id - next_client

        #num_containers = self.redis.hlen('all_containers')
        num_containers = int(self.redis.get('num_containers'))

        max_containers = self.redis.get('max_containers')
        max_containers = int(max_containers) if max_containers else self.MAX_CONT

        if diff <= (max_containers - num_containers):
            self.redis.incr('next_client')
            return enc_id, -1

        else:
            self.redis.expire('q:' + str(client_id), self.Q_EXPIRE_TIME)
            return enc_id, client_id - next_client

    def throttle(self):
        timings = self.redis.lrange('init_timings', 0, -1)
        if not timings:
            return False

        timings = self.redis.mget(*timings)

        avg = 0
        count = 0
        for val in timings:
            if val is not None:
                avg += float(val)
                count += 1

        if count == 0:
            return False

        avg = avg / count

        print('AVG: ', avg)
        throttle_max_avg = float(self.redis.get('throttle_max_avg'))
        if avg >= throttle_max_avg:
            print('Throttling, too slow...')
            return True

        return False

    def do_init(self, browser, url, ts, host, client_id):
        env = {}
        env['URL'] = url
        env['TS'] = ts
        env['SCREEN_WIDTH'] = os.environ.get('SCREEN_WIDTH')
        env['SCREEN_HEIGHT'] = os.environ.get('SCREEN_HEIGHT')
        env['REDIS_HOST'] = dc.REDIS_HOST
        env['PYWB_HOST_PORT'] = dc.PYWB_HOST + ':8080'
        env['BROWSER'] = browser

        info = self.timed_new_container(browser, env, host, client_id)
        info['queue'] = 0
        return info

    def get_randompage(self):
        if not self.randompages:
            return '/'

        url, ts = random.choice(self.randompages).split(' ', 1)
        print(url, ts)
        path = random.choice(self.browser_paths.keys())
        return '/' + path + '/' + ts + '/' + url


# Routes Below
# ===================

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
@jinja2_view('replay.html', template_lookup=['templates'])
def route_load_url(path='', url='', ts=''):
    browser = dc.browser_paths.get(path)

    if not browser:
        if path == 'random':
            path = random.choice(dc.browser_paths.keys())
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
            'browser': browser_info}


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

#run(host='0.0.0.0', port='9020')

