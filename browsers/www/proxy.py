from bottle import request, route, HTTPResponse, run
from argparse import ArgumentParser

import requests

pywb_prefix = 'localhost'
proxy_host = '10.0.2.2'
start_ts = '1990'
start_url = ''

ALLOWED_HEADERS = ('content-type', 'content-length', 'location', 'date',
                   'last-modified', 'set-cookie', 'server', 'content-encoding')

@route('/default.html')
def do_default():
    return do_proxy(start_ts + '/' + start_url)


@route('/all/<url:re:.*>')
def do_proxy(url):
    headers = {'User-Agent': request.environ.get('HTTP_USER_AGENT'),
               'Host': proxy_host,
               'Accept-Encoding': 'identity',
              }

    r = requests.get(url=pywb_prefix + url, headers=headers,
                     stream=True,
                     allow_redirects=False)

    resp_headers = []
    for n, v in r.headers.iteritems():
        if n == 'content-type':
            v = v.split(';')[0].strip()

        if n.lower() in ALLOWED_HEADERS:
            resp_headers.append((n, v))

    resp = HTTPResponse(body=r.iter_content(8192),
                        status=str(r.status_code) + ' ' + r.reason,
                        headers=resp_headers)

    return resp


if __name__ == "__main__":
    parser = ArgumentParser('netcapsule http1.0 proxy')
    parser.add_argument('--pywb-prefix')
    parser.add_argument('--start-url')
    parser.add_argument('--start-ts')
    parser.add_argument('--port', type=int)

    r = parser.parse_args()

    global pywb_prefix
    pywb_prefix = r.pywb_prefix

    global start_ts
    start_ts = r.start_ts

    global start_url
    start_url = r.start_url

    port = r.port or 8081

    run(host='0.0.0.0', port=port)

