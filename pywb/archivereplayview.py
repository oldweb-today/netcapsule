from pywb.webapp.handlers import WBHandler
from pywb.utils.statusandheaders import StatusAndHeaders
from pywb.webapp.replay_views import ReplayView, CaptureException
from pywb.rewrite.url_rewriter import UrlRewriter
from pywb.rewrite.rewrite_live import LiveRewriter
from pywb.utils.timeutils import timestamp_to_sec
from pywb.utils.loaders import BlockLoader

from redisclient import redisclient

import requests
import re
import logging

import xml.etree.ElementTree as ElementTree
import urlparse


#=============================================================================
WBURL_RX = re.compile('(.*/)([0-9]{1,14})(\w{2}_)?(/https?://.*)')
EXTRACT_ORIG_LINK = re.compile(r'<([^>]+)>;\s*rel=\"original\"')


#=============================================================================
class ReplayHandler(WBHandler):
    def _init_replay_view(self, config):
        return ReplayView(UpstreamArchiveLoader(config), config)


#=============================================================================
class MementoHandler(ReplayHandler):
    def _init_replay_view(self, config):
        return ReplayView(MementoUpstreamArchiveLoader(config), config)

    def handle_query(self, wbrequest, cdx_lines, output):
        try:
            offset = int(wbrequest.wb_url.timestamp)
            if offset < 1:
                offset = 1
        except Exception as e:
            offset = 1

        cdx_json = None
        if output != 'text':
            cdx_lines = list(cdx_lines)

            try:
                cdx_json = [dict(host=cdx['src_host'], ts=cdx['timestamp']) for cdx in cdx_lines]
                cdx_json = json.dumps(cdx_json)
            except Exception as e:
                logging.debug(e)

            cdx_lines = iter(cdx_lines)

        return self.index_reader.make_cdx_response(wbrequest,
                                                   cdx_lines,
                                                   output,
                                                   offset=offset,
                                                   cdx_json=cdx_json)


#=============================================================================
class UpstreamArchiveLoader(object):
    def __init__(self, config):
        self.session = requests.Session()
        self.session.max_redirects = 6
        self.archive_template = config['archive_template']
        self.archive_name = config['archive_name']

        # init redis here only
        redisclient.init_redis(config)

    def _do_req(self, urls, host, env, skip_hosts):
        response = None

        headers = {}
        user_agent = env.get('HTTP_USER_AGENT', '')

        # disable gzip, as mosaic won't support it!
        # TODO: maybe ungzip later
        if 'NCSA_Mosaic' in user_agent:
            headers={'Accept-Encoding': 'identity'}

        for url in urls:
            response = self.session.request(method='GET',
                                            url=url,
            #                                allow_redirects=False,
                                            headers=headers,
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
                    skip_hosts.append(host)
                    return None

                 # try again
                continue

            # success
            return response

        return response

    def __call__(self, cdx, skip_hosts, cdx_loader, wbrequest):
        self.session.cookies.clear()

        try_urls, host, archive_name = self._get_urls_to_try(cdx, skip_hosts, wbrequest)

        try:
            response = self._do_req(try_urls, host, wbrequest.env, skip_hosts)
        except Exception as e:
            print(e)
            response = None

        if response is None:
            print(skip_hosts)
            raise CaptureException('Content Could Not Be Loaded')

        remote = wbrequest.env.get('REMOTE_ADDR')
        req_ts = wbrequest.wb_url.timestamp
        base_key = remote + ':' + req_ts

        sec = timestamp_to_sec(cdx['timestamp'])
        redisclient.redis.hset(base_key + ':urls', cdx['url'], sec)
        redisclient.redis.sadd(base_key + ':hosts', archive_name)

        statusline = str(response.status_code) + ' ' + response.reason

        headers = response.headers.items()

        stream = response.raw

        status_headers = StatusAndHeaders(statusline, headers)

        return (status_headers, stream)

    def _get_urls_to_try(self, cdx, skip_hosts, wbrequest):
        if self.archive_template in skip_hosts:
            raise Exception('Content Not Available')

        #full_url = self.archive_template + wbrequest.coll + '/' + cdx['timestamp'] + 'id_/' + url
        full_url = self.archive_template.format(timestamp=cdx['timestamp'],
                                              url=cdx['url'])

        try_urls = [full_url]
        return try_urls, self.archive_template, self.archive_name


#=============================================================================
class MementoUpstreamArchiveLoader(UpstreamArchiveLoader):
    def __init__(self, config):
        super(MementoUpstreamArchiveLoader, self).__init__(config)
        self.load_archive_info_xml(config.get('memento_archive_xml'))

    def load_archive_info_xml(self, url):
        self.archive_infos = {}
        logging.debug('Loading XML from {0}'.format(url))
        if not url:
            return

        try:
            stream = BlockLoader().load(url)
        except Exception as e:
            logging.debug(e)
            logging.debug('Proceeding without xml archive info')
            return

        root = ElementTree.fromstring(stream.read())

        for link in root.findall('link'):
            name = link.get('id')
            longname = link.get('longname')
            archive = link.find('archive')
            timegate = link.find('timegate')

            if timegate is None or archive is None:
                continue

            rewritten = (archive.get('rewritten-urls') == 'yes')
            unrewritten_url = archive.get('un-rewritten-api-url', '')
            uri = timegate.get('uri')

            self.archive_infos[name] = {'uri': uri,
                                        'rewritten': rewritten,
                                        'unrewritten_url': unrewritten_url,
                                        'name': longname
                                        }

    def find_archive_info(self, host):
        host = host.split(':')[0]
        for name, info in self.archive_infos.iteritems():
            if host in info['uri']:
                return info
        return None


    def _get_urls_to_try(self, cdx, skip_hosts, wbrequest):
        src_url = cdx['src_url']
        parts = urlparse.urlsplit(src_url)
        archive_host = parts.netloc

        if archive_host in skip_hosts:
            raise CaptureException('Skipping already failed: ' + archive_host)

        info = self.find_archive_info(archive_host)

        if info and info['unrewritten_url']:
            orig_url = info['unrewritten_url'].format(timestamp=cdx['timestamp'],
                                                      url=cdx['url'])
            try_urls = [orig_url]
        else:
            try_urls = [src_url]

        wbrequest.urlrewriter.rewrite_opts['orig_src_url'] = cdx['src_url']
        wbrequest.urlrewriter.rewrite_opts['archive_info'] = info
        return try_urls, archive_host, info['name']


#=============================================================================
class ReUrlRewriter(UrlRewriter):
    def __init__(self, *args, **kwargs):
        self.session = None
        super(ReUrlRewriter, self).__init__(*args, **kwargs)

    def rewrite(self, url, mod=None):
        info = self.rewrite_opts.get('archive_info')

        # if archive info exists, and unrewrtten api exists,
        # or archive is not rewritten, use as is
        # (but add regex check for rewritten urls just in case, as they
        # may pop up in Location headers)
        if info and (info['unrewritten_url'] or not info['rewritten']):
            m = WBURL_RX.match(url)
            if m:
                if not mod:
                    mod = self.wburl.mod
                return self.prefix + m.group(2) + mod + m.group(4)
            else:
                return super(ReUrlRewriter, self).rewrite(url, mod)

        # Use HEAD request to get original url
        else:
           # don't rewrite certain urls at all
            if not url.startswith(self.NO_REWRITE_URI_PREFIX):
                url = self.urljoin(self.rewrite_opts.get('orig_src_url'), url)
                url = self.head_memento_orig(url)

            return super(ReUrlRewriter, self).rewrite(url, mod)

    def head_memento_orig(self, url):
        try:
            if not self.session:
                self.session = requests.Session()

            logging.debug('Loading HEAD Memento Headers from ' + url)
            r = self.session.head(url)
            link = r.headers.get('Link')
            if link:
                m = EXTRACT_ORIG_LINK.search(link)
                if m:
                    url = m.group(1)
                    logging.debug('Found Original: ' + url)

        except Exception as e:
            logging.debug(e)

        finally:
            return url

    def _create_rebased_rewriter(self, new_wburl, prefix):
        return ReUrlRewriter(new_wburl, prefix)
