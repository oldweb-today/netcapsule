from pywb.webapp.handlers import WBHandler
from pywb.utils.statusandheaders import StatusAndHeaders
from pywb.webapp.replay_views import ReplayView, CaptureException
from pywb.rewrite.url_rewriter import UrlRewriter
from pywb.utils.timeutils import timestamp_to_sec

import requests
import re
import redis


#=============================================================================
WBURL_RX = re.compile('(.*/)([0-9]{1,14})(\w{2}_)?(/https?://.*)')
REDIS_HOST = 'memoframe_redis_1'
#REDIS_HOST = 'localhost'

#=============================================================================
class ReplayHandler(WBHandler):
    def _init_replay_view(self, config):
        return ReplayView(LiveDirectLoader(config), config)



#=============================================================================
class LiveDirectLoader(object):
    def __init__(self, config):
        self.session = requests.Session()
        self.session.max_redirects = 6
        self.archive_prefix = config['archive_prefix']
        self.redis = redis.StrictRedis(host=REDIS_HOST)

    def _do_req(self, urls, skip_hosts):
        response = None
        for url in urls:
            response = self.session.request(method='GET',
                                            url=url,
            #                                allow_redirects=False,
                                            headers={'Accept-Encoding': 'identity'},
                                            stream=True,
                                            verify=False)

            if response is None:
                continue

            mem_date_time = response.headers.get('memento-datetime')

            if (response.status_code >= 400 and not mem_date_time):
                # assume temp failure, can try again
                if response.status_code == 503:
                    return None

                elif response.status_code == 403 or response.status_code >= 500:
                    # don't try again
                    skip_hosts.append(self.archive_prefix)
                    return None

                 # try again
                continue

            # success
            return response

        return response

    def __call__(self, cdx, skip_hosts, cdx_loader, wbrequest):
        if self.archive_prefix in skip_hosts:
            raise Exception('Content Not Available')

        url = cdx['url']
        full_url = self.archive_prefix + wbrequest.coll + '/' + cdx['timestamp'] + 'id_/' + url
        try_urls = [full_url]

        try:
            response = self._do_req(try_urls, skip_hosts)
        except Exception as e:
            response = None

        if response is None:
            print(skip_hosts)
            raise CaptureException('Content Could Not Be Loaded')

        remote = wbrequest.env.get('REMOTE_ADDR')
        req_ts = wbrequest.wb_url.timestamp
        key = remote + ':' + req_ts + ':urls'

        sec = timestamp_to_sec(cdx['timestamp'])
        self.redis.hset(key, cdx['url'], sec)

        statusline = str(response.status_code) + ' ' + response.reason

        headers = response.headers.items()

        stream = response.raw

        status_headers = StatusAndHeaders(statusline, headers)

        return (status_headers, stream)


#=============================================================================
class ReUrlRewriter(UrlRewriter):
    def rewrite(self, url, mod=None):
        m = WBURL_RX.match(url)
        if m:
            if not mod:
                mod = self.wburl.mod
            return self.prefix + m.group(2) + mod + m.group(4)
        else:
            return super(ReUrlRewriter, self).rewrite(url, mod)

    def _create_rebased_rewriter(self, new_wburl, prefix):
        return ReUrlRewriter(new_wburl, prefix)
