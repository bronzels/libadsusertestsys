from random import shuffle
from enum import Enum
import json
import copy
from math import ceil
from abc import abstractmethod
import traceback
import logging

from libpycommon.common import mystring, mylog
from libadsusertestsys.common.utils import get_serv_resp, MyError, ERR_CODE_UNKNOWN


class TestType(Enum):
    """测评类型枚举"""
    VOCAB_ESTIMATION = 'vocab-estimation'
    LISTENING_EVALUATION = 'listening-evaluation'
    SPEAKING_EVALUATION = 'speaking-evaluation'
    GRAMMAR_EVALUATION = 'grammar-evaluation'
    READING_EVALUATION = 'reading-evaluation'

    @staticmethod
    def is_direct_answer_by_value(test_type_str):
        if test_type_str == TestType.SPEAKING_EVALUATION.value:
            return True
        else:
            return False


class TestOrientation(Enum):
    """测评方向枚举"""
    UNIT_TEST = "unit-test"
    PLACEMENT_TEST = "placement-test"


class ConfusionsType(Enum):
    """测评选项类型枚举"""
    Picture = 'picture'
    Text = 'text'


class ReadingMaterialType(Enum):
    """阅读测评阅读材料类型枚举"""
    Picture = 'picture'
    Text = 'text'


class XFIseGroup(Enum):
    """讯飞语音中文测评group枚举"""
    ADULT = 'adult'
    YOUTH = 'youth'
    PUPIL = 'pupil'


class XFIseCategory(Enum):
    """讯飞语音英语测评category枚举"""
    READ_WORD = 'read_word'  # 词语朗读
    READ_SENTENCE = 'read_sentence'  # 句子朗读
    READ_CHAPTER = 'read_chapter'  # 篇章朗读
    SIMPLE_EXPRESSION = 'simple_expression'  # 英文情景反应
    READ_CHOICE = 'read_choice'  # 英文选择题
    TOPIC = 'topic'  # 英文自由题
    RETELL = 'retell'  # 英文复述题
    PICTURE_TALK = 'picture_talk'  # 英文看图说话
    ORAL_TRANSLATION = 'oral_translation'  # 英文口头翻译


class UserGrade(Enum):
    default = 255
    prekdgt = -3
    kdgt_1 = -2
    kdgt_2 = -1
    kdgt_3 = 0
    grade_1 = 1
    grade_2 = 2
    grade_3 = 3
    grade_4 = 4
    grade_5 = 5
    grade_6 = 6
    grade_7 = 7
    grade_8 = 8
    grade_9 = 9
    grade_10 = 10
    grade_11 = 11
    grade_12 = 12

    @classmethod
    def get_variables(cls):
        return [getattr(cls, attr) for attr in dir(cls) if not callable(getattr(cls, attr)) and not attr.startswith("__")]

    def get_acadsoc_level(self):
        if self.value == 255:
            return 6
        elif self.value <= 0:
            return 0
        elif self.value < 7:
            return ceil(self.value / 2)
        elif self.value <= 9:
            return 3 + (self.value - 6)
        else:
            return 6

    @classmethod
    def get_acadsoc_levels(cls):
        return set([u.get_acadsoc_level() for u in cls.get_variables()])


USER_LEVEL_DEFAULT = 255


class EntityTestQuestion:
    def __init__(self, question_id, stem, bucket, question_rev_id):
        self.question_id = question_id
        self.stem = stem
        self.bucket = bucket
        self.question_rev_id = question_rev_id

    @abstractmethod
    def get_d(self):
        return None

    @abstractmethod
    def instantiate_test_question(self):
        return None


class MultipleChoiceTestQuestion(EntityTestQuestion):
    def __init__(self, question_id, stem, bucket, question_rev_id, correct_answer, confusions, analysis, option_type):
        super().__init__(question_id, stem, bucket, question_rev_id)
        self.analysis = analysis
        self.correct_answer = correct_answer
        self.confusions = confusions
        self.option_type = option_type
        self.default_option = "以上选项都不正确"
        self.correct_option_index = None
        self.correct_option = None
        self.options = None

    def __str__(self):
        return "{}\t{}\t{}\t".format(self.stem, self.bucket, self.confusions)

    def get_d(self):
        d = {
            #'question_id': self.question_id,
            'stem': self.stem,
            #'bucket': self.bucket,
            'correct_answer': self.correct_option,
            'options': self.options
            #'confusions': self.confusions
        }
        return d

    def instantiate_test_question(self):
        ret = copy.deepcopy(self)
        options = copy.deepcopy(ret.confusions) + [ret.correct_answer]
        shuffle(options)
        orig_correct_option_index = options.index(ret.correct_answer)
        if len(options) <= 2:
            ret.correct_option = ret.correct_answer
            mylog.logger.debug('ret.correct_option:{}'.format(ret.correct_option))
        else:
            options[-1] = ret.default_option
            ret.correct_option = ret.correct_answer if (
                    orig_correct_option_index != (len(options) - 1)) else ret.default_option
            mylog.logger.debug('ret.correct_option:{}'.format(ret.correct_option))

        mylog.logger.debug('options:{}'.format(options))
        ret.options = options
        ret.correct_option_index = orig_correct_option_index
        return ret


class TrueOrFalseQuestion(EntityTestQuestion):
    def __init__(self, question_id, stem, bucket, question_rev_id, correct_answer, analysis):
        super().__init__(question_id, stem, bucket, question_rev_id)
        self.analysis = analysis
        self.correct_option = correct_answer
        self.options = ["True", "False"]
        self.correct_option_index = None

    def get_d(self):
        d = {
            'stem': self.stem,
            'correct_answer': self.correct_option,
            'options': self.options,
            'article': self.analysis
        }
        return d

    def instantiate_test_question(self):
        ret = copy.deepcopy(self)
        if ret.correct_option == "True":
            ret.correct_option_index = 0
        else:
            ret.correct_option_index = 1
        return ret


class EntityTestQuestionAndAnswer:
    def __init__(self, question):
        self.question = question
        self.answer = None

    def is_correct(self, test_type):
        if not self.answer:
            raise ValueError("Question Not Answered Yet")
        if test_type != TestType.SPEAKING_EVALUATION:
            return int(self.question.correct_option == self.answer)
        else:
            #d_speaking_answer = json.loads(self.answer)
            d_speaking_answer = self.answer
            return d_speaking_answer['total_score'] >= 60


class UserTestResult:
    def __init__(self, openid, score, level, rate_of_beaten):
        self.openid = openid
        self.score = score
        self.level = level
        self.rate_of_beaten = rate_of_beaten


def get_internal_error_catched(d_data, fn, *kwargs):
    try:
        return fn(*kwargs)
    except MyError as me:
        return get_serv_resp(d_data, code=me.code, msg=me.additional_msg, subcode=me.subcode)
    except Exception as e:
        return get_serv_resp(d_data, code=ERR_CODE_UNKNOWN, msg=str(e))

class ResponseData:
    def __init__(self, openid):
        self._d = {"openid": openid}

    def get_d(self):
        return self._d

    def get_d_decoed_yat(self, d_yat:dict):
        self._d = dict(self._d, **d_yat)
        return self

    def get_serv_resp(self, code=0, msg=None):
        return get_serv_resp(self._d, code, msg)


def get_internal_error_catched_user_req(openid, fn, *kwargs):
    d_data = {'openid': openid}
    try:
        return fn(openid, *kwargs)
    except MyError as me:
        return get_serv_resp(d_data, code=me.code, msg=me.additional_msg, subcode=me.subcode)
    except Exception as e:
        code = ERR_CODE_UNKNOWN
        if mylog.logger.getEffectiveLevel() == logging.DEBUG:
            d={
                'exception' : str(e),
                'stack': traceback.format_exc()
            }
            msg = json.dumps(d)
        else:
            msg = str(e)
        return get_serv_resp(d_data, code=code, msg=msg)


class ResponseQuestionData(ResponseData):
    def __init__(self, openid, question:MultipleChoiceTestQuestion, rate_of_progress, should_finish,
                 estimate_score, estimated_level, rate_of_beaten):
        super().__init__(openid)
        self.question = question
        self.rate_of_progress = rate_of_progress
        self.should_finish = should_finish
        self.estimate_score = estimate_score
        self.estimate_level = estimated_level
        self.rate_of_beaten = rate_of_beaten

    def get_d_decoed(self):
        d = super().get_d()
        if self.question:
            d["question"] = self.question
        else:
            d["question"] = None
        d["rate_of_progress"] = self.rate_of_progress
        d["should_finish"] = self.should_finish
        if self.should_finish:
            d["estimate_score"] = self.estimate_score
            d["estimate_level"] = self.estimate_level
            d["rate_of_beaten"] = self.rate_of_beaten
        return self


class ResponseResultData(ResponseData):
    def __init__(self, openid, result):
        super().__init__(openid)
        self.result = result

    def get_d_decoed(self):
        d = super().get_d()
        if self.result != None:
            d["result"] = self.result
        return self


def format_file_url(file_url_prefix, db_path):
    return '' if mystring.is_empty(
        db_path) else file_url_prefix + '/' + db_path


if __name__ == '__main__':
    pass
