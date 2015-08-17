from docker.client import Client
from docker.utils import kwargs_from_env

from selenium import webdriver
from selenium.webdriver.common.proxy import *

from bottle import route, run, template, request, default_app, jinja2_view
#from pprint import pprint
import requests
import os
import time


BUILD_PATH = '/browser'
MEMOFRAME_TAG = 'mf_browser'
VNC_PORT = 6080
VERSION='1.18'
PYWB_HOST = 'memoframe_pywb_1'
PYWB_HOST_PORT = 'memoframe_pywb_1:8080'


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
        #print(list(response))

    def new_container(self):
        container = self.cli.create_container(image=MEMOFRAME_TAG,
                                              ports=[VNC_PORT])
        id_ = container.get('Id')

        res = self.cli.start(container=id_,
                             port_bindings={VNC_PORT: None},
                             links={PYWB_HOST: PYWB_HOST})

        vnc_port = self.cli.port(id_, VNC_PORT)
        vnc_port = vnc_port[0]['HostPort']

        info = self.cli.inspect_container(id_)
        ip = info['NetworkSettings']['IPAddress']

        cont_info = {'id': id_,
                     'vnc_port': vnc_port,
                     'cont_ip': ip}

        self.all_containers[id_] = cont_info
        return cont_info

    def remove_all(self):
        for id_ in self.all_containers.iter_keys():
            self.cli.kill(id_)
            self.cli.remove_container(id_)

    def find_cont(self, id_):
        return self.all_containers.get(id_)


def make_proxy(proxy_host):
    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_host,
        'ftpProxy': proxy_host,
        'sslProxy': proxy_host,
        'noProxy': ''
    })
    return proxy


def load_browser(url=''):
    cont = dc.new_container()
    sel_url = 'http://{0}:4444/wd/hub'.format(cont['cont_ip'])
    print(sel_url)

    caps = webdriver.DesiredCapabilities.FIREFOX.copy()
    proxy = make_proxy(PYWB_HOST_PORT)
    proxy.add_to_capabilities(caps)

    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.accept_untrusted_certs = True

    retries = 0
    while True:
        try:
            driver = webdriver.Remote(command_executor=sel_url, browser_profile=firefox_profile, desired_capabilities=caps)
            driver.maximize_window()
            break
        except Exception as e:
            retries = retries + 1
            print(e)
            print('Retrying ', retries)
            time.sleep(5)
            if retries >= 10:
                break

    if url:
        if '://' not in url:
            url = 'http://' + url

        #driver.get(url)
        try:
            driver.set_script_timeout(1)
            driver.execute_async_script('window.location.href = "{0}"'.format(url))
        except Exception:
            pass

    return {'id': cont['id'],
            'vnc_port': cont['vnc_port']}


def set_timestamp(id_, timestamp):
    cont = dc.find_cont(id_)
    if not cont:
        return {'error': 'invalid container'}

    params = {'ts': timestamp,
              'ip': cont['cont_ip']}

    r = requests.get('http://set.pywb.proxy/', params=params, proxies={'http': PYWB_HOST_PORT})
    if r.status_code == 200:
        return {'success': r.json()}
    else:
        return {'error': r.body}


@route(['/load', '/load/<url:re:.*>'])
@jinja2_view('replay.html', template_lookup=['templates'])
def route_load_url(url=''):
    results = load_browser(url)
    print(results)
    host = request.environ.get('HTTP_HOST')
    host = host.split(':')[0]
    host = host + ':' + results['vnc_port']
    return {'host': host,
            'id': results['id']}

@route('/set')
def route_set_ts():
    ts = request.query.get('ts')
    id_ = request.query.get('id')
    return set_timestamp(id_, ts)


dc = DockerController()

dc.build_container()

application = default_app()

#run(host='0.0.0.0', port='9000')
