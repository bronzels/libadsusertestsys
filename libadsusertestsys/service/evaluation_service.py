from gevent.pywsgi import WSGIServer
import time
from flask import request
from prometheus_client import start_wsgi_server, Summary, Counter
from multiprocessing import Process

# Create a metric to track time spent and requests made.
INF_LAG_NAME_FMT = 'inflag{}'
INF_LAG_DESC_FMT = 'Time spent processing request for INF {}'
INF_COUNTER_NAME_FMT = 'infcounter{}'
INF_COUNTER_DESC_FMT = 'Counter of requests processed for INF {}'

from libpycommon.common import mylog
from libadsusertestsys.dao.evaluation_dao import *
from libadsusertestsys.entity.evaluation_entity import *
from libadsusertestsys.common.utils import *
from libadsusertestsys.redis_module.common_test_redis_tool import TestRedisTool
from libadsusertestsys.orm.config import d_question_rev2id, default_question_rev_id

def set_question_in_cache(openid, question, test_orientation, estimator_redis):
    estimator_redis.add_last_question(test_orientation.value, openid, question)


def set_batch_question_in_cache(openid, questions, test_orientation, estimator_redis):
    estimator_redis.add_batch_questions(test_orientation.value, openid, questions)


def set_test_result_in_cache(openid, test_result, test_orientation, estimator_redis):
    estimator_redis.add_test_result(test_orientation.value, openid, test_result)


def evaluate_algorithm(openid, test_type, test_orientation, evaluation_estimator, evaluation_redis, question_rev_id):
    if evaluation_redis.exists_test_result(test_orientation.value, openid):
        last_question = evaluation_redis.get_last_question(test_orientation.value, openid)
        mylog.logger.debug('last_question:{}'.format(last_question.__dict__))
        user_test_result = evaluation_redis.get_test_result(test_orientation.value, openid)
        mylog.logger.debug('user_test_result:{}'.format(user_test_result))
        mylog.logger.warn('Test result is already exists in redis, no need to evluation again and catch,openid:{}'
                          .format(openid))
        evaluation_result = ResponseQuestionData(
            openid, last_question.question.get_d(), 100, True,
            user_test_result['score'], user_test_result['level'], user_test_result['rate_of_beaten'])
        return evaluation_result

    should_finish = False
    estimated_score = None
    estimated_level = None
    rate_of_beaten = None

    if evaluation_redis.exists_question_and_answer(test_orientation.value, openid):
        user_questions_and_answers = evaluation_redis.get_all_questions_in_order(test_orientation.value, openid)
        mylog.logger.debug('user_questions_and_answers:{}'.format(user_questions_and_answers))
    else:
        user_questions_and_answers = []
        user = get_user_by_openid(openid)
        if user is None:
            mylog.logger.warning("user is not created before question got")
            on_create_user(openid, "Unknown")

    rate_of_progress = int(len([x for x in user_questions_and_answers if x.answer is not None]) / evaluation_estimator.max_question_request * 100)
    mylog.logger.info('rate_of_progress:{}'.format(rate_of_progress))
    if len(user_questions_and_answers) == 0:
        next_question = evaluation_estimator.get_next_question(user_questions_and_answers, question_rev_id)
        mylog.logger.info('next_question:{}'.format(next_question))
        next_question_and_answer = EntityTestQuestionAndAnswer(next_question)
        mylog.logger.debug('next_question_and_answer:{}'.format(next_question_and_answer))
        set_question_in_cache(openid, next_question_and_answer, test_orientation, evaluation_redis)
    elif len(user_questions_and_answers) > 0 and user_questions_and_answers[-1].answer is None:
        mylog.logger.warning("previous question not answered yet")
        last_unanswered_question = user_questions_and_answers[-1]
        mylog.logger.debug('last_unanswered_question:{}'.format(last_unanswered_question))
        next_question = last_unanswered_question.question
    else:
        next_question = evaluation_estimator.get_next_question(user_questions_and_answers, question_rev_id)
        mylog.logger.info('next_question:{}'.format(next_question))
        # TODO: 对单个bucket内答题数累计达到一定阈值也应做判断是否应该结束（现在题目数为10道，可能不需要对单个bucket做判断，
        #  但是为了代码通用性，加上为宜）
        if not next_question:
            should_finish = True
        elif len(user_questions_and_answers) >= evaluation_estimator.max_question_request:
            should_finish = True
        else:
            should_finish = False

        if should_finish:
            last_question_and_answer = user_questions_and_answers[-1]
            mylog.logger.debug('last_question_and_answer:{}'.format(last_question_and_answer))
            next_question = last_question_and_answer.question
            if test_type != TestType.VOCAB_ESTIMATION:
                estimated_score, estimated_level = evaluation_estimator.estimate_algorithm(test_type, user_questions_and_answers)
            else:
                estimated_score, estimated_level = evaluation_estimator.estimate_algorithm(user_questions_and_answers, question_rev_id)
            mylog.logger.info('estimated_score:{}, estimated_level:{}'.format(estimated_score, estimated_level))
            rate_of_progress = 100
            right_answers = len(list(filter(lambda q: q.is_correct(test_type) == 1, user_questions_and_answers)))
            if right_answers == 0:
                rate_of_beaten = 0.1
            elif len(user_questions_and_answers) == right_answers:
                rate_of_beaten = 0.9
            else:
                scores = get_test_result_by_test_info_and_level(
                    evaluation_estimator.test_type.value, test_orientation.value, int(estimated_level.split("_")[1]))
                mylog.logger.debug('scores:{}'.format(scores))
                rate_of_beaten = evaluation_estimator.estimate_rate_of_beaten(scores,
                                                                              int(estimated_level.split("_")[1]),
                                                                              estimated_score)
            mylog.logger.debug('rate_of_beaten:{}'.format(rate_of_beaten))
            rate_of_beaten = round(rate_of_beaten, 2)
            user_test_result = UserTestResult(openid, estimated_score, estimated_level, rate_of_beaten)
            mylog.logger.debug('user_test_result:{}'.format(user_test_result.__dict__))
            set_test_result_in_cache(openid, user_test_result, test_orientation, evaluation_redis)
        else:
            next_question_and_answer = EntityTestQuestionAndAnswer(next_question)
            set_question_in_cache(openid, next_question_and_answer, test_orientation, evaluation_redis)

    evaluation_result = ResponseQuestionData(
        openid, next_question.get_d(), rate_of_progress, should_finish, estimated_score, estimated_level, rate_of_beaten)
    return evaluation_result


def serve_forever(app, evaluation_estimators, test_type, evaluation_redis, myver):
    def _route_2_name(route):
        return route.replace('/', '_')

    def _get_metrics_summary(route):
        return Summary(INF_LAG_NAME_FMT.format(_route_2_name(route)), INF_LAG_DESC_FMT.format(_route_2_name(route)))

    def _get_metrics_counter(route):
        return Counter(INF_COUNTER_NAME_FMT.format(_route_2_name(route)), INF_COUNTER_DESC_FMT.format(_route_2_name(route)))

    @app.route("/", methods=["GET"])
    def ver():
        return get_serv_ver(myver)

    @app.route("/set/log", methods=["GET"])
    def set_loglevel():
        request_data = request_parse(request)
        return get_serv_set_loglevel(request_data)

    def _get_test_orientation_json(request_data):
        # TODO：下个版本加入unit，所有测评接口和general的/get/user/last/result必须传入test_orientation参数，
        # 如果是TestOrientation.UNIT_TEST，必须还传入'unit'参数
        # TestOrientation.PLACEMENT_TEST
        test_orientation_str = "placement-test"
        # test_orientation_str = request_data.get("test_orientation_str")
        return test_orientation_str

    def _get_test_orientation_form(request):
        # TODO：下个版本加入unit，所有测评接口和general的/get/user/last/result必须传入test_orientation参数，
        # 如果是TestOrientation.UNIT_TEST，必须还传入'unit'参数
        # TestOrientation.PLACEMENT_TEST
        test_orientation_str = "placement-test"
        # test_orientation_str = request.form.get('test_orientation')
        return test_orientation_str

    def _get_estimator(openid, test_orientation):
        user = get_user_by_openid(openid)
        if user is None:
            raise MyError(ERR_CODE_OPENID_NOT_EXISTS)
        user_grade = user.grade
        if user_grade is None:
            raise MyError(ERR_CODE_GRADE_NOT_SET)
        mylog.logger.info('user_grade:{}'.format(user_grade))
        user_acadsoc_level = UserGrade(user_grade).get_acadsoc_level()
        mylog.logger.info('user_acadsoc_level:{}'.format(user_acadsoc_level))
        # evaluation_estimator = evaluation_estimators[test_orientation.value][UserGrade.default.value]
        # evaluation_estimator = evaluation_estimators[test_orientation.value][user_grade]
        evaluation_estimator = evaluation_estimators[test_orientation.value][user_acadsoc_level]
        return evaluation_estimator

    INF_ROUTE_get_question = "/get/question"
    INF_LAG_get_question = _get_metrics_summary(INF_ROUTE_get_question)
    INF_COUNTER_get_question = _get_metrics_counter(INF_ROUTE_get_question)
    @app.route(INF_ROUTE_get_question, methods=["GET"])
    #@INF_LAG_get_question.time()
    def get_question():
        #INF_COUNTER_get_question.inc()
        def _req_fn():
            request_data = request_parse(request)
            openid = request_data.get("openid")
            if openid is None:
                raise MyError(ERR_CODE_INF_INPUT_ABSENT, 'openid:{}'.format(openid))
            test_orientation_str = _get_test_orientation_json(request_data)
            mylog.logger.info('openid:{}, test_orientation_str:{}'.format(openid, test_orientation_str))
            def _req_fn_user_req(openid, test_orientation_str):
                test_orientation = TestOrientation(test_orientation_str)
                question_rev_id = default_question_rev_id
                question_rev = request_data.get("question_rev")
                if question_rev is not None:
                    if question_rev in d_question_rev2id:
                        question_rev_id = d_question_rev2id[question_rev]
                    else:
                        raise MyError(ERR_CODE_INF_INPUT_INVALID, additional_msg='question_rev:{}'.format(question_rev))
                mylog.logger.info('test_orientation:{}'.format(test_orientation.__dict__))
                evaluation_estimator = _get_estimator(openid, test_orientation)
                rqdata_result = evaluate_algorithm(openid, test_type, test_orientation, evaluation_estimator, evaluation_redis, question_rev_id)
                mylog.logger.info('rqdata_result:{}'.format(rqdata_result.__dict__))
                code = 0
                msg = None
                return rqdata_result.get_d_decoed().get_serv_resp(code, msg)
            return get_internal_error_catched_user_req(openid, _req_fn_user_req, test_orientation_str)
        return get_internal_error_catched({}, _req_fn)

    def _update_answer(openid, answer, test_orientation_str, is_by_post=True):
        #INF_COUNTER_update_answer.inc()
        start = int(time.time() * 1000)
        # 更新缓存答题结果
        mylog.logger.info('openid:{}, test_orientation_str:{}'.format(openid, test_orientation_str))
        mylog.logger.debug('answer:\n{}'.format(answer))
        def _req_fn_user_req(openid, answer, test_orientation_str):
            test_orientation = TestOrientation(test_orientation_str)
            mylog.logger.info('test_orientation:{}'.format(test_orientation.__dict__))
            d_data_2deco = {}
            code = 0
            msg = None
            if not evaluation_redis.exists_question_and_answer(test_orientation.value, openid):
                code = 1003
            else:
                if test_type == TestType.SPEAKING_EVALUATION:
                    audio_file = answer
                    test_orientation = TestOrientation(test_orientation_str)
                    mylog.logger.info('test_orientation:{}'.format(test_orientation.__dict__))
                    evaluation_estimator = _get_estimator(openid, test_orientation)
                    user_last_question = evaluation_redis.get_last_question(test_orientation_str, openid)
                    mylog.logger.debug('user_last_question:{}'.format(user_last_question.__dict__))
                    code, message, d_data_2deco, answer = evaluation_estimator.get_result_by_auto_recog_service(
                        openid, user_last_question, audio_file, is_by_post)
                else:
                    if not is_by_post:
                        answer = str(answer.read(), encoding='utf-8')
                if code == 0:
                    user_last_question = evaluation_redis.pop_last_question(test_orientation.value, openid)
                    user_last_question.answer = answer
                    mylog.logger.debug('user_last_question:{}'.format(user_last_question.__dict__))
                    evaluation_redis.add_last_question(test_orientation.value, openid, user_last_question)
            rspdata = ResponseData(openid)
            mylog.logger.info('rspdata:{}'.format(rspdata.__dict__))
            end = int(time.time() * 1000)
            mylog.logger.info('REST /update/answer lag:{}'.format(end - start))
            return rspdata.get_d_decoed_yat(d_data_2deco).get_serv_resp(code, msg)
        return get_internal_error_catched_user_req(openid, _req_fn_user_req, answer, test_orientation_str)

    INF_ROUTE_update_answer = "/update/answer"
    INF_LAG_update_answer = _get_metrics_summary(INF_ROUTE_update_answer)
    INF_COUNTER_update_answer = _get_metrics_counter(INF_ROUTE_update_answer)
    @app.route(INF_ROUTE_update_answer, methods=["POST"])
    #@INF_LAG_update_answer.time()
    def update_answer():
        #INF_COUNTER_update_answer.inc()
        def _req_fn():
            request_data = request_parse(request, "json")
            openid = request_data.get("openid")
            answer = request_data.get("answer")
            test_orientation_str = _get_test_orientation_json(request_data)
            return _update_answer(openid, answer, test_orientation_str, True)
        return get_internal_error_catched({}, _req_fn)

    INF_ROUTE_update_fileanswer = "/update/fileanswer"
    INF_LAG_update_fileanswer = _get_metrics_summary(INF_ROUTE_update_fileanswer)
    INF_COUNTER_update_fileanswer = _get_metrics_counter(INF_ROUTE_update_fileanswer)
    @app.route(INF_ROUTE_update_fileanswer, methods=["POST"])
    #@INF_LAG_update_fileanswer.time()
    def update_fileanswer():
        #INF_COUNTER_update_fileanswer.inc()
        def _req_fn():
            openid = request.form.get('openid')
            answer = request.files['answer']
            if openid is None or answer is None:
                raise MyError(ERR_CODE_INF_INPUT_ABSENT, 'openid:{}, answer:{}'.format(openid, answer))
            answer_read = answer.stream
            test_orientation_str = _get_test_orientation_form(request)
            return _update_answer(openid, answer_read, test_orientation_str, False)
        return get_internal_error_catched({}, _req_fn)

    INF_ROUTE_reset = "/reset"
    INF_LAG_reset = _get_metrics_summary(INF_ROUTE_reset)
    INF_COUNTER_reset = _get_metrics_counter(INF_ROUTE_reset)
    @app.route(INF_ROUTE_reset, methods=["GET"])
    #@INF_LAG_reset.time()
    def reset():
        #INF_COUNTER_reset.inc()
        def _req_fn():
            request_data = request_parse(request)
            openid = request_data.get("openid")
            if openid is None:
                raise MyError(ERR_CODE_INF_INPUT_ABSENT, 'openid:{}'.format(openid))
            test_orientation_str = _get_test_orientation_json(request_data)
            mylog.logger.info('openid:{}, test_orientation_str:{}'.format(openid, test_orientation_str))
            def _req_fn_user_req(openid, test_orientation_str):
                test_orientation = TestOrientation(test_orientation_str)
                code = 0
                msg = ''
                exists_test_result = False
                if evaluation_redis.exists_test_result(test_orientation.value, openid):
                    exists_test_result = True
                    user_test_result = evaluation_redis.get_test_result(test_orientation.value, openid)
                    mylog.logger.debug('user_test_result:{}'.format(user_test_result))
                    test_result_id = save_test_result(openid, test_type.value, test_orientation.value,
                                                      float(user_test_result['score']),
                                                      int(user_test_result['level'].split("_")[1]),
                                                      float(user_test_result['rate_of_beaten']))
                    evaluation_redis.delete_test_result(test_orientation.value, openid)
                else:
                    submsg = "User has no test result, no need to reset,openid:{}".format(openid)
                    mylog.logger.debug(submsg)
                    msg += submsg + '\n'

                if evaluation_redis.exists_question_and_answer(test_orientation.value, openid):
                    user_question_and_answers = evaluation_redis.get_all_questions_in_order(test_orientation.value,
                                                                                            openid)
                    mylog.logger.debug('user_question_and_answers:{}'.format(user_question_and_answers))
                    if exists_test_result:
                        batch_create_user_question_and_answer(test_type, openid, test_result_id,
                                                              [x for x in user_question_and_answers if
                                                               x.answer is not None])

                    evaluation_redis.delete_question_and_answer_key_all(test_orientation.value, openid)
                else:
                    submsg = "There is a round of test results but no list of test questions. " \
                             "It may have not been reset in time and the cache was partially cleared,openid:{}".format(
                        openid)
                    mylog.logger.debug(submsg)
                    msg += submsg
                return ResponseResultData(openid, None).get_d_decoed().get_serv_resp(code, msg)
            return get_internal_error_catched_user_req(openid, _req_fn_user_req, test_orientation_str)
        return get_internal_error_catched({}, _req_fn)

def entry(port, myver, test_type, fn_generate_estimators):
    from libadsusertestsys.orm.app import SERVER_ADDR, DATABASE, USER_ACCOUNT, SECURIT_CODE
    mylog.logger.debug(
        'SERVER_ADDR:{},DATABASE:{},USER_ACCOUNT:{},SECURIT_CODE:{}'.format(SERVER_ADDR, DATABASE, USER_ACCOUNT,
                                                                            SECURIT_CODE))
    from libadsusertestsys.orm.config import BOOL_DEBUG_SWITCH, FILES_URL_PREFIX
    mylog.logger.debug('DEBUG_SWITCH:{},FILES_URL_PREFIX:{}'.format(BOOL_DEBUG_SWITCH, FILES_URL_PREFIX))
    from libadsusertestsys.redis_module.redis_pool import REDIS_HOST, REDIS_PORT, REDIS_PASSWD, REDIS_MAX_CONN, REDIS_EXPIRE_TIME
    mylog.logger.debug(
        'REDIS_HOST:{},REDIS_PORT:{},REDIS_PASSWD:{},REDIS_MAX_CONN:{},REDIS_EXPIRE_TIME:{}'.format(REDIS_HOST, REDIS_PORT, REDIS_PASSWD,
                                                                               REDIS_MAX_CONN, REDIS_EXPIRE_TIME))
    from libadsusertestsys.orm.config import XUNFEI_APIKEY, XUNFEI_APISECRET, XUNFEI_APPID
    mylog.logger.debug(
        'XUNFEI_APIKEY:{},XUNFEI_APISECRET:{},XUNFEI_APPID:{}'.format(XUNFEI_APIKEY, XUNFEI_APISECRET, XUNFEI_APPID))

    # Start up the server to expose the metrics.
    METRICS_PORT = int(misc.get_env('METRICS_PORT', '8090'))
    bind_addr = '0.0.0.0'
    #start_wsgi_server(METRICS_PORT, addr=bind_addr)

    INTERFACE_PORT = int(misc.get_env('INTERFACE_PORT', port))

    from libadsusertestsys.orm.user_test_sys_orm import app
    evaluation_redis = TestRedisTool(test_type)
    serve_forever(app, fn_generate_estimators(), test_type, evaluation_redis, myver)
    wsgi_server = WSGIServer((bind_addr, INTERFACE_PORT), app)
    wsgi_server.serve_forever()
    '''
    for i in range(2):
        wsgi_server = WSGIServer((bind_addr, INTERFACE_PORT+i), app)
        p = Process(target=wsgi_server.serve_forever())
        p.start()
    '''
