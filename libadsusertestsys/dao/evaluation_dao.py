import json

from libpycommon.common import mylog
from libadsusertestsys.orm.user_test_sys_orm import *
from libadsusertestsys.entity.evaluation_entity import TestType


def on_create_user(openid, session_key=None, inviter_openid=None):
	user = get_user_by_openid(openid)
	if user is None:
		test_user = TestUser(
			openid=openid,
			session_key=session_key,
			inviter_openid=inviter_openid)
		save_test_user(test_user)
		return 1
	else:
		mylog.logger.warn("user with openid {} already exist!!!".format(openid))
		return 0


def save_test_user(test_user):
	db.session.add(test_user)
	db.session.commit()


def save_estimation_test_question(evaluation_test_question):
	db.session.add(evaluation_test_question)
	db.session.commit()


def create_test_question(test_type_str, subject_question_id):
	test_question = TestQuestion(
		test_type=test_type_str,
		subject_question_id=int(subject_question_id))
	save_test_question(test_question)


def save_test_question(test_question):
	db.session.add(test_question)
	db.session.commit()


def batch_create_user_question_and_answer(test_type, openid, test_result_id, question_and_answers):
	user = get_user_by_openid(openid)
	if user is None:
		mylog.logger.warn("Warning! User not exist with openid {}!!!".format(openid))
	else:
		if test_type != TestType.SPEAKING_EVALUATION:
			test_question_and_answers = [
				TestQuestionAndAnswer(
					test_user_id=user.id,
					test_question_id=int(question_and_answer.question.question_id),
					test_result_id=test_result_id,
					test_answer=question_and_answer.answer,
					is_correct=question_and_answer.is_correct(test_type)
				)
				for question_and_answer in question_and_answers
			]
		else:
			test_question_and_answers = [
				SpeakingTestQuestionAndAnswer(
					test_user_id=user.id,
					test_question_id=int(question_and_answer.question.question_id),
					test_result_id=test_result_id,
					test_user_audio_path=question_and_answer.answer['test_user_audio_path'],
					category=question_and_answer.answer['category'],
					is_nonsense=question_and_answer.answer['is_nonsense'],
					accuracy_score=question_and_answer.answer['accuracy_score'],
					standard_score=question_and_answer.answer['standard_score'],
					fluency_score=question_and_answer.answer['fluency_score'],
					integrity_score=question_and_answer.answer['integrity_score'],
					total_score=question_and_answer.answer['total_score']
				)
				for question_and_answer in question_and_answers
			]
		db.session.add_all(test_question_and_answers)
		db.session.commit()


def save_test_result(openid, test_type_str, test_orientation_str, score, level, rate_of_beaten):
	user = get_user_by_openid(openid)
	if user is None:
		mylog.logger.warn("Warning! User not exist with openid {}!!!".format(openid))
		return None

	test_result = TestResult(
		test_user_id=user.id,
		test_type=test_type_str,
		test_orientation=test_orientation_str,
		score=score,
		acadsoc_level=level,
		rate_of_beaten=rate_of_beaten,
	)
	db.session.add(test_result)
	db.session.commit()
	ret = test_result.id
	return ret



def get_user_by_openid(openid):
	return TestUser.query.filter_by(openid=openid).first()


def get_test_result_by_test_type_and_level(test_type_str, level):
	return TestResult.query.filter_by(test_type=test_type_str, level=level).all()


def get_test_result_by_test_info_and_level(test_type_str, test_orientation_str, level):
	return TestResult.query.filter_by(test_type=test_type_str, test_orientation=test_orientation_str, acadsoc_level=level).all()


def get_question_by_type_and_subject_question_id(test_type_str, subject_question_id):
	return TestQuestion.query.filter_by(test_type=test_type_str, subject_question_id=int(subject_question_id)).first()


def get_all_answered_question_by_user_id(test_user_id):
	return TestQuestionAndAnswer.query.filter_by(test_user_id=test_user_id)


def get_test_result_by_all_info(test_user_id, test_type_str, test_orientation_str, score, level, rate_of_beaten, create_time):
	return TestResult.query.filter_by(
		test_user_id=test_user_id, test_type=test_type_str, score=score, level=level,
		test_orientation=test_orientation_str, rate_of_beaten=rate_of_beaten,
		create_time=create_time).first()


def get_test_user_count():
	return db.session.query(TestUser.id).count()


def update_user_info(test_user, age=None, phone_number=None, uid=None, grade=None):
	ret = dict()
	ret['age'] = 0
	ret['phone_number'] = 0
	ret['uid'] = 0
	ret['grade'] = 0
	if age is not None and test_user.age != age:
		test_user.age = age
		ret['age'] = 1
	if phone_number is not None and test_user.phone_number != phone_number:
		test_user.phone_number = phone_number
		ret['phone_number'] = 1
	if uid is not None and test_user.uid != uid:
		test_user.uid = uid
		ret['uid'] = 1
	if grade is not None and test_user.grade != grade:
		test_user.grade = grade
		ret['grade'] = 1
	db.session.commit()
	return ret


def update_user_age(openid, age):
	test_user = get_user_by_openid(openid=openid)
	if test_user is None:
		return 0

	test_user.age = age
	db.session.commit()
	return 1


def update_user_phone_number(openid, phone_number):
	user = get_user_by_openid(openid=openid)
	if user is None:
		return 0

	user.phone_number = phone_number
	db.session.commit()
	return 1


def update_user_uid(openid, uid):
	user = get_user_by_openid(openid=openid)
	if user is None:
		return 0

	user.uid = uid
	db.session.commit()
	return 1


def get_last_test_result(test_user_id, test_type_str, test_orientation_str):
	return TestResult.query.filter_by(
		test_user_id=test_user_id, test_type=test_type_str, test_orientation=test_orientation_str).order_by(TestResult.create_time.desc()).first()


def get_last_test_result_grouped(test_user_id):
	'''
	subquery = db.session.query(
		TestResult,
		func.row_number().over(
			order_by=TestResult.create_time.desc(),
			partition_by=[TestResult.test_type, TestResult.test_orientation]
	).label('rnk')
	).subquery()
	ret = [item for item in db.session.query(TestResult).select_entity_from(subquery).filter(
		TestResult.test_user_id == test_user_id, subquery.c.rnk == 1
	)]
	'''
	cursor = db.session.execute('SELECT create_time,test_type, test_orientation, acadsoc_level FROM (SELECT create_time,test_user_id, test_type, test_orientation, acadsoc_level, ROW_NUMBER() OVER(PARTITION BY test_type, test_orientation ORDER BY id DESC) AS rnk FROM TestResult WHERE test_user_id={}) ranked WHERE rnk=1'.format(test_user_id))
	result = cursor.fetchall()
	ret = [item for item in result]
	return ret


def get_placement_test_questions_by_test_type_and_level_interval(orm_entity, min_level, max_level, l_question_rev_id):
	return orm_entity.query.filter(
		orm_entity.acadsoc_level >= min_level, orm_entity.acadsoc_level <= max_level).filter(
		orm_entity.question_rev_id.in_(l_question_rev_id)).order_by(orm_entity.id.asc()).all()


def get_test_question_rev(obsolete=False):
	d_question_rev = {}
	l_question_rev_id = []
	l_question_rev = TestQuestionRev.query.filter_by(
		obsolete=obsolete)
	for i in l_question_rev:
		d_question_rev[i.question_rev] = i.id
		l_question_rev_id.append(i.id)
	return d_question_rev, l_question_rev_id
