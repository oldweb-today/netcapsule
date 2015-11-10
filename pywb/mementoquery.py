import requests
import sys
import calendar
import datetime
import itertools
import urllib
import json

from collections import namedtuple

from pywb.utils.canonicalize import canonicalize
from pywb.utils.timeutils import iso_date_to_datetime, datetime_to_timestamp
from pywb.utils.timeutils import timestamp_to_sec
from pywb.utils.wbexception import AccessException, NotFoundException

import logging
from urlparse import urlsplit

from redisclient import redisclient


EXCLUDE_LIST = ('http://archive.today/', 'http://archive.is', 'https://archive.today/', 'https://archive.is/', 'http://arquivo.pt')


#=============================================================================
def datetime_to_secs(dt):
    return calendar.timegm(dt.utctimetuple())


#=============================================================================
MemValue = namedtuple('MemValue', 'ts, sec, url')


#=============================================================================
class MementoJsonApi(object):
    def __init__(self, paths):
        self.api_endpoint = paths['timegate']
        self.timemap_endpoint = paths['timemap']
        self.session = requests.Session()

    def timegate_query(self, timestamp, url):
        url = urllib.quote(url, ':/')
        full = self.api_endpoint + timestamp + '/' + url
        r = None
        try:
            r = self.session.get(full)
            result = r.json()
        except Exception as e:
            if not r or r.status_code != 404:
                import traceback
                traceback.print_exc(e)

            msg = 'No Mementos Found'
            raise NotFoundException(msg, url=url)

        return result['mementos']

    def timemap_query(self, url, closest='1'):
        url = urllib.quote(url, ':/')
        full = self.timemap_endpoint + closest + '/' + url
        r = None
        try:
            r = self.session.get(full)
            result = r.json()
        except Exception as e:
            logging.debug(e)
            if r and r.status_code == 503:
                msg = 'No Mementos Currently Available: <br/>'
                msg += r.text
            elif r and r.status_code == 404:
                return {"list": []}
            elif r:
                msg = 'Unknown response with: ' + str(r.status_code)
            else:
                msg = 'No response'

            raise NotFoundException(msg, url=url)

        mementos = result.get('mementos')
        # if got timemap_index, just cached the timemap, so need to query again
        # TODO: revisit this..
        if not mementos and result.get('timemap_index'):
            return self.timemap_query(url, closest)

        return mementos

    def parse_mem_value(self, m):
        iso = m['datetime']
        dt = iso_date_to_datetime(iso)
        sec = datetime_to_secs(dt)
        ts = datetime_to_timestamp(dt)
        url = m['uri']

        return MemValue(ts, sec, url)


#=============================================================================
class MementoTimemapQuery(object):
    def __init__(self, api_loader, url, closest='1'):
        self.api_loader = api_loader
        self.closest = closest
        self.url = url

    def __iter__(self):
        mementos = self.api_loader.timemap_query(self.url, self.closest)
        self.memento_list = mementos['list']
        self.memento_iter = iter(self.memento_list)

        return self

    def next(self):
        return (self.api_loader.parse_mem_value(self.memento_iter.next()),)


#=============================================================================
class MementoClosestQuery(object):
    """ Provides an iterator over memento JSON API, returning
    results closest to the requested timestamp, and checking
    next-closest which each iteration
    """
    def __init__(self, api_loader, url, timestamp):
        self.api_loader = api_loader
        self.url = url
        self.target_timestamp = timestamp
        self.target_sec = timestamp_to_sec(timestamp)

    def _get_mem_info(self, mementos, name, closest_ts=None):
        m = mementos.get(name)
        if not m:
            return None

        parsed = self.api_loader.parse_mem_value(m)
        if not parsed:
            return None

        if parsed.ts == closest_ts:
            return None

        return parsed

    def __iter__(self):
        mementos = self.api_loader.timegate_query(self.target_timestamp, self.url)

        self.m_closest = self._get_mem_info(mementos, 'closest')

        closest_ts = None
        if self.m_closest:
            closest_ts = self.m_closest.ts

        self.m_next = self._get_mem_info(mementos, 'next', closest_ts)
        self.m_prev = self._get_mem_info(mementos, 'prev', closest_ts)

        self.m_last = self._get_mem_info(mementos, 'last', closest_ts)
        self.m_first = self._get_mem_info(mementos, 'first', closest_ts)

        return self

    def next(self):
        if not self.m_closest:
            if self.m_next and self.m_prev:
                if (abs(self.m_next.sec - self.target_sec) <
                    abs(self.m_prev.sec - self.target_sec)):
                    self.set_next_closest(self.m_next)
                else:
                    self.set_next_closest(self.m_prev)

            elif not self.m_next and self.m_prev:
                self.set_next_closest(self.m_prev)
            elif self.m_next and not self.m_prev:
                self.set_next_closest(self.m_next)

        if self.m_closest:
            res = self.m_closest
            self.m_closest = None
            return (res, self.m_next, self.m_prev, self.m_first, self.m_last)
        else:
            raise StopIteration()

    def set_next_closest(self, curr):
        mementos = self.api_loader.timegate_query(curr.ts, self.url)
        self.m_closest = self._get_mem_info(mementos, 'closest')

        if curr == self.m_next:
            self.m_next = self._get_mem_info(mementos, 'next', curr.ts)

        elif curr == self.m_prev:
            self.m_prev = self._get_mem_info(mementos, 'prev', curr.ts)


#=============================================================================
class MementoIndexServer(object):
    def __init__(self, paths, **kwargs):
        self.loader = MementoJsonApi(paths)
        #logging.basicConfig(level=logging.DEBUG)

    def load_cdx(self, **params):
        sort = params.get('sort')
        if sort == 'closest' or sort == 'reverse':
            closest = params.get('closest')
            if not closest:
                closest = str(datetime.date.today().year)


            mem_iter = redisclient.load_cdx_cache_iter(params['url'], closest)
            if mem_iter:
                return mem_iter

            mem_iter = MementoClosestQuery(self.loader, params['url'], closest)

            skip_exclude=True
            timegate = True

        else:
            closest = params.get('query_closest')
            try:
                closest = int(closest)
                if closest < 1:
                    closest = '1'
                else:
                    closest = str(closest)
            except:
                closest = '1'

            mem_iter = MementoTimemapQuery(self.loader, params['url'], closest)

            skip_exclude=False
            timegate = False

        limit = int(params.get('limit', 10))

        mem_iter = self.memento_to_cdx(params['url'],
                                       mem_iter,
                                       limit,
                                       skip_exclude)

        if timegate:
            mem_iter = redisclient.save_cdx_cache_iter(mem_iter, params['url'], closest)


        if params.get('output') == 'text':
            mem_iter = self.cdx_to_text(mem_iter)

        return mem_iter

    def sort_archives(self, archive_list):
        ait = None
        ia = None
        pt = None
        for url in archive_list:
            if '/web.archive.org/' in url:
                ia = url
            elif '/wayback.archive-it.org/' in url:
                ait = url
            elif '/arquivo.pt/' in url:
                pt = url
            elif '/archive.today/' in url:
                continue
            else:
                yield url

        if ait:
            yield ait

        if ia:
            yield ia

        if pt:
            yield pt

    def memento_to_cdx(self, url, mem_iter, limit, skip_exclude=True):
        key = canonicalize(url)
        if url.endswith('/'):
            key += '/'

        for mems, _ in itertools.izip(mem_iter, xrange(0, limit)):

            if len(mems) > 1:
                mem, next_, prev_, first_, last_ = mems
            else:
                mem = mems[0]

            excluded = False

            if isinstance(mem.url, list):
                mem_list = mem.url
                count = len(mem_list)
                if count > 1:
                    mem_list = self.sort_archives(mem_list)
            else:
                mem_list = [mem.url]
                count = 1

            for mem_url in mem_list:
                mem_url = mem_url.encode('utf-8')
                # handle scheme relative urls
                if mem_url.startswith('//'):
                    mem_url = 'http:' + mem_url

                if mem_url.startswith(EXCLUDE_LIST):
                    if skip_exclude:
                        continue
                    else:
                        excluded = True

                cdx = {}
                cdx['urlkey'] = key
                cdx['timestamp'] = mem.ts
                cdx['url'] = url
                cdx['src_url'] = mem_url
                cdx['sec'] = mem.sec
                cdx['src_host'] = urlsplit(mem_url).netloc
                cdx['excluded'] = excluded
                cdx['dupes'] = count

                if len(mems) > 1:
                    cdx['first'] = first_.ts if first_ else ''
                    cdx['last'] = last_.ts if last_ else ''
                    cdx['next'] = next_.ts if next_ else ''
                    cdx['prev'] = prev_.ts if prev_ else ''
                yield cdx

    def cdx_to_text(self, cdx_list):
        for cdx in cdx_list:
            string = cdx['urlkey'] + ' ' + cdx['timestamp']
            del cdx['urlkey']
            del cdx['timestamp']
            string += ' ' + json.dumps(cdx) + '\n'
            yield string


def test_memento_to_cdx(url, mem):
    key = canonicalize(url)
    for ts, target in mem:
        yield key + ' ' + ts + ' ' + url + ' ' + target


def main():
    server = MementoIndexServer(['http://timetravel.mementoweb.org/api/json/',
                                 'http://timetravel.mementoweb.org/timemap/json/'])
    redisclient.init_redis()

    cdx_iter = server.load_cdx(closest=sys.argv[1],
                               url=sys.argv[2],
                               sort='closest',
                               limit=int(sys.argv[3]))
    sec = None
    for cdx in cdx_iter:
        if not sec:
            sec = cdx['sec']
        #print(cdx['timestamp'] + ' ' + cdx['url'] + ' ' + cdx['src_host'] + ' ' + str(sec - cdx['sec']))
        print(cdx['prev'] + ' ' + cdx['timestamp'] + ' ' + cdx['next'] + ' ' + str(sec - cdx['sec']))


if __name__ == "__main__":
    main()
