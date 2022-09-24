import os
import base64
import json
# from subprocess import DEVNULL, STDOUT, check_call
import logging
from flask import jsonify, make_response

from libpycommon.common import mylog
from libpycommon.common import misc
from libpycommon.common import cmd
from libpycommon.common.misc import get_env


BOOL_DEBUG_SWITCH = misc.get_env('DEBUG_SWITCH', 'off') == 'on'
BOOL_FAKE_SWITCH = misc.get_env('FAKE_SWITCH', 'on') == 'on'

ERR_CODE_success = 0#	成功
ERR_CODE_INF_INPUT_INVALID = 999#	非法输入参数
ERR_CODE_INF_INPUT_ABSENT = 1000#	缺少输入参数
ERR_CODE_OPENID_ALREADY_EXISTS = 1001#	openid对应用户已存在
ERR_CODE_OPENID_NOT_EXISTS = 1002#	openid对应用户不存在
ERR_CODE_NO_QUESTIONS_ANSWERED = 1003#	用户还未答题
ERR_CODE_ALL_QUESTIONS_ANSWERED = 1004#	用户已完成答题
ERR_CODE_GRADE_NOT_SET = 1005#	用户grade还未设置
ERR_CODE_EXTERNAL_KNOWN = 1100#	外部服务调用已知错误
ERR_CODE_EXTERNAL_UNKNOWN = 1101#	外部服务调用未知错误
ERR_CODE_EXTERNAL_ALLOWANCE = 1102#	外部服务调用量超出限额
ERR_CODE_IO_CACHE = 2000#	访问缓存系统错误
ERR_CODE_IO_DB = 2001#	访问数据库错误
ERR_CODE_IO_FILE = 2002#	访问文件系统错误
ERR_CODE_IO_NETWORK = 2003#	访问网络错误
ERR_CODE_UNKNOWN = 3000#	内部错误

d_err_code_msg = {
    ERR_CODE_success: '成功',
    ERR_CODE_INF_INPUT_INVALID: '非法输入参数',
    ERR_CODE_INF_INPUT_ABSENT: '缺少输入参数',
    ERR_CODE_OPENID_ALREADY_EXISTS: 'openid对应用户已存在',
    ERR_CODE_OPENID_NOT_EXISTS: 'openid对应用户不存在',
    ERR_CODE_NO_QUESTIONS_ANSWERED: '用户还未答题',
    ERR_CODE_ALL_QUESTIONS_ANSWERED: '用户已完成答题',
    ERR_CODE_GRADE_NOT_SET: '用户grade还未设置',
    ERR_CODE_EXTERNAL_KNOWN: '外部服务调用已知错误',
    ERR_CODE_EXTERNAL_UNKNOWN: '外部服务调用未知错误',
    ERR_CODE_EXTERNAL_ALLOWANCE: '外部服务调用量超出限额',
    ERR_CODE_IO_CACHE: '访问缓存系统错误',
    ERR_CODE_IO_DB: '访问数据库错误',
    ERR_CODE_IO_FILE: '访问文件系统错误',
    ERR_CODE_IO_NETWORK: '访问网络错误',
    ERR_CODE_UNKNOWN: '内部错误',
}

d_err_code_msg_xunfei = {
10163:'参数校验失败，由客户端参数校验失败引起，客户端需要依据返回的message字段中的描述来更改请求参数',
10313:'请求参数 第一帧没有传app_id 或者传 的app_id 与api_key 不匹配。',
40007:'音频解码失败，请检查所传的音频是否与encoding字段描述的编码格式对应。',
11201:'接口使用量超出了购买的最大限制，请购买后继续使用。',
10114:'请求超时，会话时间超过了300s，请控制会话时间，保持不超过300s',
10043:'音频解码失败，请确保所传音频编码格式与请求参数保持一致。',
10161:'base64解码失败，检查发送的数据是否使用base64编码了',
10200:'读取数据超时，检查是否累计10s未发送数据并且未关闭连接',
10160:'请求数据格式非法，检查请求数据是否是合法的json',
11200:'功能未授权',
60114:'评测音频长度过长',
10139:'参数错误',
48196:'实例禁止重复调用该接口',
40006:'无效参数',
40010:'无响应',
40016:'初始化失败',
40017:'没有初始化',
40023:'无效配置',
40034:'参数未设置',
40037:'无评测文本',
40038:'无评测语音',
40040:'非法数据',
42306:'授权数不够',
68676:'乱说',
30002:'ssb没有cmd参数',
48195:'实例评测试卷未设置，试题格式错误，请检查评测文本是否与试题匹配，特别是英文题型需要在试题中加特殊标记、未设置ent、category等参数等',
30011:'sid为空，如上传音频未设置aus',
68675:'不正常的语音数据，请检查是否为16k、16bit、单声道音频，并且检查aue参数值指定是否与音频类型匹配',
48205:'实例未评测，如没有获取到录音、上传音频为空导致的报错',
}

d_err_code_msg_sub = {
    ERR_CODE_EXTERNAL_KNOWN:d_err_code_msg_xunfei
}

class MyError(ValueError):
    def __init__(self, code, additional_msg=None, subcode=None):
        self.code = code
        self.additional_msg = additional_msg
        self.subcode = subcode


def request_parse(user_request, mode="args"):
    '''解析请求数据并以json形式返回'''
    if mode == "args":
        data = user_request.args
    else:
        data = json.loads(user_request.get_data().decode("utf-8"))
    return data


def replace_all(word, char, rep_char):
    while char in word:
        word = word.replace(char,rep_char)
    return word


class lazy(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val

def base64_to_file(base64_data, file_path, file_name):
    """
    base64文件转存二进制文件

    :param base64_data: base64字符串
    :param file_path: 文件保存路径
    :param file_name: 文件名
    :return 无
    """
    origin_image_data = base64.b64decode(base64_data.split(',')[1])
    extensions = base64_data.split(',')[0].rsplit('/')[1].split(';')
    path = file_path + "/" + file_name + "." + extensions[0]
    with open(path, 'wb') as f:
        f.write(origin_image_data)
    f.close()
    return path

def get_serv_ver(myver):
    d = {
        'name': misc.get_env('SERV_NAME'),
        'ver': myver,
        'log_level': logging.getLevelName(mylog.logger.getEffectiveLevel())
    }
    return json.dumps(d)

def get_serv_set_loglevel(request_data):
    loglevel_name = request_data.get("level")
    mylog.logger.info('loglevel_name:{}'.format(loglevel_name))
    loglevel_value = None
    if loglevel_name is not None:
        loglevel_value = mylog.get_level_from_name(loglevel_name)
    mylog.logger.info('loglevel_value:{}'.format(loglevel_value))
    mylog.logger.info('mylog.logger.getEffectiveLevel():{}'.format(mylog.logger.getEffectiveLevel()))
    err_msg = ''
    if loglevel_value is not None:
        mylog.logger.setLevel(loglevel_value)
    else:
        err_msg = 'loglevel_name:{}, error converted to level'.format(loglevel_name)
        mylog.logger.error(err_msg)
    mylog.logger.info('mylog.logger.getEffectiveLevel():{}'.format(mylog.logger.getEffectiveLevel()))
    d = {
        'code':0 if loglevel_value is not None else -1,
        'msg': err_msg
    }
    return json.dumps(d)

def format_response(data, code=0, msg=""):
    response = {
        "data": data,
        "code": code,
        "msg": msg
    }
    return response

def get_serv_resp(d_data, code=ERR_CODE_success, msg=None, subcode=None):
    retmsg = ''
    if code != ERR_CODE_success:
         if subcode is not None:
             submsg = d_err_code_msg_sub[code][subcode]
             retmsg = '{}，详细：{}'.format(d_err_code_msg[code], submsg)
         else:
            retmsg = '{}'.format(d_err_code_msg[code])
    if msg is not None:
        retmsg += '，补充：{}'.format(msg)
    d_resp = format_response(d_data, code, retmsg)
    response = make_response(jsonify(d_resp))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def set_log_level_from_env():
    loglevel_name = get_env('LOG_LEVEL', 'warning')
    loglevel_value = mylog.get_level_from_name(loglevel_name)
    if loglevel_value is None:
        raise ValueError('wrong loglevel_name:{}'.format(loglevel_name))
    mylog.logger.setLevel(loglevel_value)


