from selenium import webdriver
from selenium.webdriver.common.proxy import *

from bottle import route, default_app, run, request

import requests

import time
import sys


PYWB_HOST_PORT = 'memoframe_pywb_1:8080'

curr_ip = '127.0.0.1'
driver = None

def make_proxy(proxy_host):
    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_host,
        'ftpProxy': proxy_host,
        'sslProxy': proxy_host,
        'noProxy': ''
    })
    return proxy

def load_browser(url='', ts=''):
    caps = webdriver.DesiredCapabilities.FIREFOX.copy()
    proxy = make_proxy(PYWB_HOST_PORT)
    proxy.add_to_capabilities(caps)

    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.accept_untrusted_certs = True

    global driver

    retries = 0
    while True:
        try:
            #sel_url = 'http://{0}:4444/wd/hub'.format(cont['cont_ip'])
            #driver = webdriver.Remote(command_executor=sel_url, browser_profile=firefox_profile, desired_capabilities=caps)
            driver = webdriver.Firefox(firefox_profile=firefox_profile, capabilities=caps)
            driver.maximize_window()
            print('FF STARTED')
            break
        except Exception as e:
            retries = retries + 1
            print(e)
            print('Retrying ', retries)
            time.sleep(5)
            if retries >= 10:
                break

    if ts:
        set_timestamp(ts)

    if url:
        if '://' not in url:
            url = 'http://' + url

        #driver.get(url)
        try:
            driver.set_script_timeout(1)
            driver.execute_async_script('window.location.href = "{0}"'.format(url))
        except Exception:
            pass


def set_timestamp(timestamp):
    params = {'ts': timestamp,
              'ip': curr_ip}

    try:
        r = requests.get('http://set.pywb.proxy/', params=params, proxies={'http': PYWB_HOST_PORT, 'https': PYWB_HOST_PORT})

        if r.status_code == 200:
            return {'success': r.json()}
        else:
            return {'error': r.body}

    except Exception as e:
        return {'error': str(e)}


@route('/set')
def route_set_ts():
    ts = request.query.get('ts')
    res = set_timestamp(ts)

    global driver
    if driver and res.get('success'):
        try:
            driver.refresh()
        except Exception as e:
            print(e)


def do_init():
    url = ''
    ts = ''

    if len(sys.argv) > 1:
        global curr_ip
        curr_ip = sys.argv[1]

        if len(sys.argv) > 2:
            url = sys.argv[2]
            if len(sys.argv) > 3:
                ts = sys.argv[3]

    load_browser(url, ts)
    return default_app()


application = do_init()


if __name__ == "__main__":
    run(host='0.0.0.0', port='6082')

