import redis
import os
import yaml

from pywb.utils.canonicalize import canonicalize


#=============================================================================
class RedisClient(object):
    def __init__(self):
        self.redis = None

    def init_redis(self, config={}):
        if self.redis:
            return

        redis_url = os.environ.get('REDIS_URL')

        if not redis_url:
            redis_url = config.get('redis_url')

        if not redis_url:
            redis_url = 'redis://localhost:6379/0'

        if redis_url:
            self.redis = redis.StrictRedis.from_url(redis_url)
        else:
            self.redis = redis.StrictRedis()

    # CDX Caching
    def load_cdx_cache_iter(self, url, ts):
        page_key = self.get_url_key_p(ts, url)
        cdx_list = self.redis.lrange('cdx:' + page_key, 0, -1)

        if not cdx_list:
            page_key = self.redis.get('r:' + page_key)
            if page_key:
                cdx_list = self.redis.lrange('cdx:' + page_key, 0, -1)

        if not cdx_list:
            return []

        cdx_list = [yaml.load(cdx) for cdx in cdx_list]

        return cdx_list

    def save_cdx_cache_iter(self, cdx_list, url, ts):
        full_key = 'cdx:' + self.get_url_key_p(ts, url)
        for cdx in cdx_list:
            self.redis.rpush(full_key, yaml.dump(cdx))
            self.redis.expire(full_key, 180)
            yield cdx

    def pipeline(self):
        return redis.utils.pipeline(self.redis)

    @staticmethod
    def get_url_key_p(ts, url):
        key = ts + '/' + canonicalize(url, False)
        if not url.endswith('/'):
            key += '/'
        return key


#=============================================================================
redisclient = RedisClient()

