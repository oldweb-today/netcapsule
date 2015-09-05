from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view

import os
import datetime
import time
import re
import atexit

from threading import Thread


BUILD_PATH = '/browser'
MEMOFRAME_TAG = 'mf_browser'
VNC_PORT = 6080
CMD_PORT = 6082
VERSION='1.18'
PYWB_HOST = 'memoframe_pywb_1'

EXPIRE_DELTA = datetime.timedelta(seconds=300)


#=============================================================================
class DockerController(object):
    def __init__(self):
        self.all_containers = {}

        if os.path.exists('/var/run/docker.sock'):
            self.cli = Client(base_url='unix://var/run/docker.sock',
                              version=VERSION)
        else:
            kwargs = kwargs_from_env()
            kwargs['tls'].assert_hostname = False
            kwargs['version'] = VERSION
            self.cli = Client(**kwargs)

    def build_container(self):
        response = self.cli.build(BUILD_PATH, tag=MEMOFRAME_TAG, rm=True)

    def new_container(self, env=None):
        container = self.cli.create_container(image=MEMOFRAME_TAG,
                                              ports=[VNC_PORT, CMD_PORT],
                                              environment=env)
        id_ = container.get('Id')

        res = self.cli.start(container=id_,
                             port_bindings={VNC_PORT: None, CMD_PORT: None},
                             links={PYWB_HOST: PYWB_HOST})

        vnc_port = self.cli.port(id_, VNC_PORT)
        vnc_port = vnc_port[0]['HostPort']

        cmd_port = self.cli.port(id_, CMD_PORT)
        cmd_port = cmd_port[0]['HostPort']

        info = self.cli.inspect_container(id_)
        ip = info['NetworkSettings']['IPAddress']

        cont_info = {'id': id_,
                     'vnc_port': vnc_port,
                     'cmd_port': cmd_port,
                     'cont_ip': ip,
                     'last_ts': datetime.datetime.utcnow()
                    }

        self.all_containers[id_] = cont_info
        return cont_info

    def remove_all(self):
        for id_ in self.all_containers.iter_keys():
            self.cli.kill(id_)
            self.cli.remove_container(id_)

    def heartbeat(self, id_):
        cont_info = self.all_containers.get(id_)
        if not cont_info:
            return

        print('UPDATED ' + id_)
        cont_info['last_ts'] = datetime.datetime.utcnow()

    def check_abandoned(self):
        print('CHECKING ALL')
        print(self.all_containers)
        now = datetime.datetime.utcnow()
        for id_ in self.all_containers.keys():
            cont_info = self.all_containers[id_]
            print('CHECKING ' + cont_info['id'] + ' ' + cont_info['cont_ip'])
            if (now - cont_info['last_ts']) > EXPIRE_DELTA:
                print('REMOVING ' + cont_info['id'] + ' ' + cont_info['cont_ip'])
                self.cli.remove_container(id_, force=True)
                del self.all_containers[id_]

    def remove_all(self):
        for id_ in self.all_containers.keys():
            self.cli.remove_container(id_, force=True)


@route(['/web', '/web/<ts:re:[0-9-]+>/<url:re:.*>', '/web/<url:re:.*>'])
@jinja2_view('replay.html', template_lookup=['templates'])
def route_load_url(url='', ts=''):
    results = dc.new_container({'URL': url, 'TS': ts})

    host = request.environ.get('HTTP_HOST')
    host = host.split(':')[0]

    vnc_host = host + ':' + results['vnc_port']
    cmd_host = host + ':' + results['cmd_port']

    if not ts:
        ts = re.sub('[ :-]', '', str(datetime.datetime.utcnow()).split('.')[0])

    return {'vnc_host': vnc_host,
            'cmd_host': cmd_host,
            'ts': ts,
            'id': results['id']}

@route(['/ping/<cid>'])
def ping(cid):
    dc.heartbeat(cid)
    return {}

def onexit():
    dc.remove_all()

dc = DockerController()

dc.build_container()

application = default_app()

def check_abandonded():
    while True:
        dc.check_abandoned()
        time.sleep(30)

t = Thread(target=check_abandonded)
t.daemon = True
t.start()

atexit.register(onexit)

run(host='0.0.0.0', port='9020')

