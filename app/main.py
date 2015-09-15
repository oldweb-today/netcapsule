from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view

import os
import datetime
import time
import re
import atexit
import redis

from uwsgidecorators import timer
import uwsgi


BUILD_PATHS = {'/browser': 'mf_browser', '/netscape': 'mf_netscape'}

VNC_PORT = 6080
CMD_PORT = 6082
VERSION='1.18'
PYWB_HOST = 'memoframe_pywb_1'
REDIS_HOST = 'memoframe_redis_1'

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

    def build_container(self):
        for path, tag in BUILD_PATHS.iteritems():
            print(path, tag)
            response = self.cli.build(path, tag=tag, rm=True)

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
        self.redis.sadd('all_containers', short_id)
        self.redis.setex('c:' + short_id, EXPIRE_TIME, 1)

        return vnc_port, cmd_port

    def check_abandoned(self):
        all_containers = self.redis.smembers('all_containers')

        for short_id in all_containers:
            res = self.redis.get('c:' + short_id)
            if not res:
                print('REMOVING ' + short_id)
                try:
                    self.cli.remove_container(short_id, force=True)
                except Exception as e:
                    print(e)
                self.redis.srem('all_containers', short_id)

    def remove_all(self):
        all_containers = self.redis.smembers('all_containers')
        for short_id in all_containers:
            try:
                self.cli.remove_container(short_id, force=True)
            except Exception as e:
                print(e)
            self.redis.srem('all_containers', short_id)
            self.redis.delete('c:' + short_id)


@route(['/<tag:re:(ff|ns)>/<ts:re:[0-9-]+>/<url:re:.*>', '/<tag:re:(ff|ns)>/<url:re:.*>'])
@jinja2_view('replay.html', template_lookup=['templates'])
def route_load_url(tag='', url='', ts=''):
    if tag == 'ns':
        tag = 'mf_netscape'
    else:
        tag = 'mf_browser'

    vnc_port, cmd_port = dc.new_container(tag, {'URL': url, 'TS': ts})

    host = request.environ.get('HTTP_HOST')
    host = host.split(':')[0]

    vnc_host = host + ':' + vnc_port
    cmd_host = host + ':' + cmd_port

    if not ts:
        ts = re.sub('[ :-]', '', str(datetime.datetime.utcnow()).split('.')[0])

    return {'vnc_host': vnc_host,
            'cmd_host': cmd_host,
            'url': url,
            'ts': ts}

def onexit():
    dc.remove_all()

dc = DockerController()

#dc.build_container()

application = default_app()

@timer(CHECK_TIME, target='mule')
def check_abandonded(signum):
    #while True:
    dc.check_abandoned()


uwsgi.atexit = onexit

#run(host='0.0.0.0', port='9020')

