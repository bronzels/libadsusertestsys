import pickle
import logging

from libpycommon.common import mylog
from libpycommon.common import misc
from libadsusertestsys.redis_module.redis_pool import r, REDIS_EXPIRE_TIME

NAMESPACE_PREFIX = 'dtstr:model:usertest'
QUESTION_ZSET_PREFIX = NAMESPACE_PREFIX + ':qst:z'
KEY_FMT_QUESTION_AND_ANSWER_KEY_ROOT = QUESTION_ZSET_PREFIX + ':{}:{}:{}:{}'
KEY_PART_BUCKET_ALL = 'bucket_all'
KEY_FMT_MATCH_QUESTION_AND_ANSWER_KEY_ROOT = QUESTION_ZSET_PREFIX + ':{}:{}:{}:*'
KEY_FMT_TEST_RESULT_KEY_ROOT = NAMESPACE_PREFIX + ':rst:h:{}:{}:{}'

class TestRedisTool:
    def __init__(self, test_type):
        self.test_type = test_type.value

    def get_question_and_answer_key(self, test_orientation_str, user_id, bucket):
        return KEY_FMT_QUESTION_AND_ANSWER_KEY_ROOT.format(self.test_type, test_orientation_str, user_id, bucket)

    def get_question_and_answer_key_all(self, test_orientation_str, user_id):
        return self.get_question_and_answer_key(test_orientation_str, user_id, KEY_PART_BUCKET_ALL)

    def get_test_result_key(self, test_orientation_str, user_id):
        return KEY_FMT_TEST_RESULT_KEY_ROOT.format(self.test_type, test_orientation_str, user_id)

    def exists_question_and_answer(self, test_orientation_str, user_id):
        key = self.get_question_and_answer_key_all(test_orientation_str, user_id)
        return r.exists(key)

    def exists_test_result(self, test_orientation_str, user_id):
        key = self.get_test_result_key(test_orientation_str, user_id)
        return r.exists(key)

    def get_last_question(self, test_orientation_str, user_id):
        key = self.get_question_and_answer_key_all(test_orientation_str, user_id)
        last_question_l = r.zrange(key, -1, -1)
        ret = None
        if last_question_l is not None and len(last_question_l) == 1:
            ret = pickle.loads(last_question_l[0])
        return ret

    def get_test_result(self, test_orientation_str, user_id):
        key = self.get_test_result_key(test_orientation_str, user_id)
        d_data = r.hgetall(key)
        ret = {}
        try:
            for k, v in d_data.items():
                ret[k.decode()] = v.decode()
        except:
            ret = d_data
        return ret

    def pop_last_question(self, test_orientation_str, user_id):
        key = self.get_question_and_answer_key_all(test_orientation_str, user_id)
        last_question = r.zpopmax(key, 1)[0][0]
        if last_question:
            last_question = pickle.loads(last_question)
        bucket_key = self.get_question_and_answer_key(test_orientation_str, user_id, last_question.question.bucket)
        _ = r.zpopmax(bucket_key, 1)[0][0]
        return last_question

    def add_last_question(self, test_orientation_str, user_id, question):
        key = self.get_question_and_answer_key_all(test_orientation_str, user_id)
        bucket_key = self.get_question_and_answer_key(test_orientation_str, user_id, question.question.bucket)
        try:
            if not r.exists(key):
                r.zadd(key, {pickle.dumps(question): 0})
                r.zadd(bucket_key, {pickle.dumps(question): 0})
            else:
                last_zset_score = r.zcard(key)
                r.zadd(key, {pickle.dumps(question): last_zset_score})
                last_zset_score_bucket = r.zcard(bucket_key)
                r.zadd(bucket_key, {pickle.dumps(question): last_zset_score_bucket})
            r.expire(key, REDIS_EXPIRE_TIME)
            r.expire(bucket_key, REDIS_EXPIRE_TIME)
        except:
            mylog.logger.warning("Error! Unable to cache question for user {}".format(user_id))

    def get_all_questions_in_order(self, test_orientation_str, user_id):
        key = self.get_question_and_answer_key_all(test_orientation_str, user_id)
        all_questions = r.zrange(key, 0, -1)
        return [pickle.loads(i) for i in all_questions]

    def add_batch_questions(self, test_orientation_str, user_id, questions):
        while len(questions) > 0:
            last_question = questions.pop(0)
            self.add_last_question(test_orientation_str, user_id, last_question)

    def add_test_result(self, test_orientation_str, user_id, test_result):
        key = self.get_test_result_key(test_orientation_str, user_id)
        d_hash = {'score': test_result.score,
                  'level': test_result.level,
                  'rate_of_beaten': test_result.rate_of_beaten}
        if not r.exists(key):
            r.hmset(key, d_hash)
        r.expire(key, REDIS_EXPIRE_TIME)

    def delete_question_and_answer_key(self, test_orientation_str, user_id, bucket):
        question_and_answer_key = self.get_question_and_answer_key(test_orientation_str, user_id, bucket)
        r.delete(question_and_answer_key)

    def delete_question_and_answer_key_all(self, test_orientation_str, user_id):
        question_and_answer_keys = r.keys(KEY_FMT_MATCH_QUESTION_AND_ANSWER_KEY_ROOT.
                                          format(self.test_type, test_orientation_str, user_id))
        for key in question_and_answer_keys:
            r.delete(key)

    def delete_test_result(self, test_orientation_str, user_id):
        test_result_key = self.get_test_result_key(test_orientation_str, user_id)
        r.delete(test_result_key)
