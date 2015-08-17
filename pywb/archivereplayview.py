from pywb.webapp.handlers import WBHandler
from pywb.utils.statusandheaders import StatusAndHeaders
from pywb.webapp.replay_views import ReplayView, CaptureException
from pywb.rewrite.url_rewriter import UrlRewriter

import requests
import re


#=============================================================================
WBURL_RX = re.compile('(.*/)([0-9]{1,14})(\w{2}_)?(/https?://.*)')


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

    def _do_req(self, urls, skip_hosts):
        response = None
        for url in urls:
            response = self.session.request(method='GET',
                                            url=url,
            #                                allow_redirects=False,
                                            stream=True,
                                            verify=False)

            if response is None:
                continue

            mem_date_time = response.headers.get('memento-datetime')

            if (response.status_code >= 400 and not mem_date_time):
                if response.status_code == 403:
                    # don't try again
                    skip_hosts.append(archive_host)
                    return None

                elif response.status_code >= 500:
                    return None

                # try again
                continue

            # success
            return response

        return response

    def __call__(self, cdx, skip_hosts, cdx_loader, wbrequest):
        url = cdx['url']
        full_url = self.archive_prefix + wbrequest.coll + '/' + cdx['timestamp'] + 'id_/' + url
        try_urls = [full_url]

        try:
            response = self._do_req(try_urls, skip_hosts)
        except Exception as e:
            response = None

        if response is None:
            raise CaptureException('Content Could Not Be Loaded')

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
