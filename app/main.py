from docker.client import Client
from docker.utils import kwargs_from_env

from bottle import route, run, template, request, default_app, jinja2_view

import os
import datetime
import re

BUILD_PATH = '/browser'
MEMOFRAME_TAG = 'mf_browser'
VNC_PORT = 6080
CMD_PORT = 6082
VERSION='1.18'
PYWB_HOST = 'memoframe_pywb_1'


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
                     'cont_ip': ip}

        self.all_containers[id_] = cont_info
        return cont_info

    def remove_all(self):
        for id_ in self.all_containers.iter_keys():
            self.cli.kill(id_)
            self.cli.remove_container(id_)

    def find_cont(self, id_):
        return self.all_containers.get(id_)


#@route(['/load', '/load/<ts:re:[0-9-]+>/<url:re:.*>', '/load/<url:re:.*>'])
#def test(url='', ts=''):
#    return {'url': url, 'ts': ts}

@route(['/load', '/load/<ts:re:[0-9-]+>/<url:re:.*>', '/load/<url:re:.*>'])
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


dc = DockerController()

dc.build_container()

application = default_app()

#run(host='0.0.0.0', port='9000')

