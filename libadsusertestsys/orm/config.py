import os
from libpycommon.common import misc
from libadsusertestsys.common.utils import BOOL_DEBUG_SWITCH
from libadsusertestsys.dao.evaluation_dao import get_test_question_rev
from libadsusertestsys.mykey.me import package_key_res_path

# 讯飞鉴权数据
XUNFEI_APPID = misc.get_env_encrypted('XUNFEI_APPID', package_key_res_path)#'5f3b5c3c'
XUNFEI_APISECRET = misc.get_env_encrypted('XUNFEI_APISECRET', package_key_res_path)#'54de07b55a2fe56cae8eb42166c9b94c'
XUNFEI_APIKEY = misc.get_env_encrypted('XUNFEI_APIKEY', package_key_res_path)#'4e8c3e2b9244755a190c55febddcfe29'

# 多媒体文件路径（动态/静态）
FILES_URL_PREFIX = misc.get_env('FILES_URL_PREFIX')#http://192.168.0.85:21080
# OSS_IMPORT_DATE = misc.get_env('OSS_IMPORT_DATE')
# if OSS_IMPORT_DATE != '':  # 如果不用OSS文件服务器，则不应设置这个环境变量，或者将改环境变量置空
#     FILES_URL_PREFIX += '/' + OSS_IMPORT_DATE

DEFAULT_QUESTION_REV = misc.get_env('DEFAULT_QUESTION_REV', '')
_dockerv_k8spvc_mounted_files_path_root = '/mnt/analysis_group/usertestsys'
if DEFAULT_QUESTION_REV != '':
    # _dockerv_k8spvc_mounted_files_path_root += '/' + DEFAULT_QUESTION_REV
    FILES_URL_PREFIX += '/' + DEFAULT_QUESTION_REV

# 录音目录:口语
FILES_PATH_ROOT = None
if BOOL_DEBUG_SWITCH:
    import files
    path = files.__file__
    FILES_PATH_ROOT = path[0:path.find('__init__.py')-1]
else:
    FILES_PATH_ROOT = _dockerv_k8spvc_mounted_files_path_root

AUDIOGEN_FILES_PATH_ROOT = FILES_PATH_ROOT + '/audiogen'
AUDIOGEN_ABSPATH_REC_AUDIO_POOL = AUDIOGEN_FILES_PATH_ROOT + '/spe'
AUDIOGEN_ABSPATH_REC_AUDIO_POOL_ORIGIN = AUDIOGEN_ABSPATH_REC_AUDIO_POOL + '/origin'
AUDIOGEN_ABSPATH_REC_AUDIO_POOL_PCM = AUDIOGEN_ABSPATH_REC_AUDIO_POOL + '/pcm'

# 生成图片目录：qrcode/general
# PICGEN_FILES_PATH_ROOT= FILES_PATH_ROOT + '/picgen'
# QRCODE_ABSPATH_ROOT= PICGEN_FILES_PATH_ROOT + '/qrc'
PICGEN_FILES_PATH_ROOT= os.path.join(FILES_PATH_ROOT, 'picgen')
QRCODE_ABSPATH_ROOT= os.path.join(PICGEN_FILES_PATH_ROOT, 'qrc')
# 生成图片地址：qrcode/general
PICGEN_URL_ROUTE_ROOT= FILES_URL_PREFIX + '/picgen'
QRCODE_URL_ROUTE_PICTURE= PICGEN_URL_ROUTE_ROOT + '/qrc'

# 音频池地址
AUDIOSTATIC_URL_ROUTE_ROOT= FILES_URL_PREFIX + '/audiostatic'

# 音频池地址：口语/听力
AUDIOSTATIC_LIS_URL_ROUTE= AUDIOSTATIC_URL_ROUTE_ROOT + '/lis'
AUDIOSTATIC_SPE_URL_ROUTE= AUDIOSTATIC_URL_ROUTE_ROOT + '/spe'

# 音频池地址：词汇/英式美式
AUDIOSTATIC_VOC_URL_ROUTE= AUDIOSTATIC_URL_ROUTE_ROOT + '/voc'
AUDIOSTATIC_VOC_EN_URL_ROUTE= AUDIOSTATIC_VOC_URL_ROUTE + '/en'
AUDIOSTATIC_VOC_US_URL_ROUTE= AUDIOSTATIC_VOC_URL_ROUTE + '/us'

# 图片池地址
PICSTATIC_URL_ROUTE_ROOT= FILES_URL_PREFIX + '/picstatic'
PICSTATIC_LIS_URL_ROUTE= PICSTATIC_URL_ROUTE_ROOT + '/lis'
PICSTATIC_SPE_URL_ROUTE= PICSTATIC_URL_ROUTE_ROOT + '/spe'
PICSTATIC_GRA_URL_ROUTE= PICSTATIC_URL_ROUTE_ROOT + '/gra'
PICSTATIC_REA_URL_ROUTE= PICSTATIC_URL_ROUTE_ROOT + '/rea'

# 返回结果形式('str':字符串，'base64':二进制流）
RESULT_XML_FORM = 'base64'

# 语音类型：'read_word' / 'read_sentence' / 'read_chapter'
SPEECH_CATEGORY = 'read_sentence'

# 题库版本
d_question_rev2id, l_question_rev_id = get_test_question_rev(obsolete=False)

default_question_rev_id = d_question_rev2id.get(DEFAULT_QUESTION_REV)
if default_question_rev_id is None:
    raise ValueError('environment variable DEFAULT_QUESTION_REV is not matched with non obsolete question_rev in table  TestQuestionRev')

# 临时文件保存目录，下载大小
FILE_DL_TMPSAVED_PATH = '/tmp'
FILE_DL_SIZE = 9000