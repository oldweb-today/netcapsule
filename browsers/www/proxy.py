from bottle import request, route, HTTPResponse, run
from argparse import ArgumentParser

import requests

proxies = 'localhost'
proxy_prefix = 'http://10.0.2.2/'
start_ts = '1990'
start_url = ''

ALLOWED_HEADERS = ('content-type', 'content-length', 'location', 'date',
                   'last-modified', 'set-cookie', 'server', 'content-encoding')

@route('/default.html')
def do_default():
    return do_proxy(url=start_url)


@route(['/<dt:re:[0-9]+([\w]{2}_)?>/<url:re:.*>', '/<url:re:.*>'])
def do_proxy(dt='', url=''):
    headers = {'User-Agent': request.environ.get('HTTP_USER_AGENT'),
               #'Host': proxy_host,
               'Accept-Encoding': 'identity',
               'Pywb-Rewrite-Prefix': proxy_prefix,
              }

    if not url.startswith('http://'):
        url = 'http://' + url

    r = requests.get(url=url, headers=headers,
                     stream=True,
                     allow_redirects=False,
                     proxies=proxies)

    resp_headers = []
    for n, v in r.headers.iteritems():
        if n.lower() == 'content-type':
            v = v.split(';')[0].strip()

        if n.lower() in ALLOWED_HEADERS:
            resp_headers.append((n, v))

    # force status code to 200 so that pages load in WWW
    # error pages are not otherwise shown at all
    status_code = r.status_code
    if status_code >= 400:
        status_code = 200

    resp = HTTPResponse(body=r.iter_content(8192),
                        status=str(status_code) + ' ' + r.reason,
                        headers=resp_headers)

    return resp


if __name__ == "__main__":
    parser = ArgumentParser('netcapsule http1.0 proxy')
    parser.add_argument('--pywb-prefix')
    parser.add_argument('--start-url')
    parser.add_argument('--start-ts')
    parser.add_argument('--port', type=int)

    r = parser.parse_args()

    global proxies
    proxies = dict(http=r.pywb_prefix,
                   https=r.pywb_prefix)

    global start_ts
    start_ts = r.start_ts

    global start_url
    start_url = r.start_url

    port = r.port or 8081

    run(host='0.0.0.0', port=port)

