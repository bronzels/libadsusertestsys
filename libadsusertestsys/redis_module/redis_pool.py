import redis

from libpycommon.common import misc
from libadsusertestsys.mykey.me import package_key_res_path

REDIS_HOST=misc.get_env('REDIS_HOST')#192.168.0.22
REDIS_PORT=int(misc.get_env('REDIS_PORT'))#6379
REDIS_PASSWD=misc.get_env_encrypted('REDIS_PASSWD', package_key_res_path)#Acadsoc@2020@Online
REDIS_MAX_CONN=int(misc.get_env('REDIS_MAX_CONN'))#10
# 测试时day设置1，上线day设置24
REDIS_EXPIRE_TIME = int(misc.get_env('REDIS_EXPIRE', 60 * 60 * 24 * 3))

pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, max_connections=REDIS_MAX_CONN, password=REDIS_PASSWD)
r = redis.StrictRedis(connection_pool=pool, decode_responses=True)
