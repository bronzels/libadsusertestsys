from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, Float
from libadsusertestsys.orm.app import create_app
from flask_sqlalchemy import SQLAlchemy
app = create_app()  # 实例化一个app对象
db = SQLAlchemy(app)  # 创建一个数据库引擎


class TestUser(db.Model):
    """测评用户信息表"""
    __tablename__ = 'TestUser'
    id = Column(Integer, autoincrement=True, primary_key=True)
    openid = Column(String(200), nullable=False, unique=True)
    session_key = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    age = Column(String(20), nullable=True)
    grade = Column(Integer, nullable=True)
    uid = Column(String(20), nullable=True)
    inviter_openid = Column(String(200), nullable=True)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class TestQuestion(db.Model):
    """测评试题记录表"""
    __tablename__ = 'TestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    test_type = Column(String(50), nullable=False)
    subject_question_id = Column(Integer)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class TestQuestionAndAnswer(db.Model):
    """用户测评试题与答题记录表"""
    __tablename__ = 'TestQuestionAndAnswer'
    id = Column(Integer, autoincrement=True, primary_key=True)
    test_user_id = Column(Integer)
    test_question_id = Column(Integer)
    test_result_id = Column(Integer)
    test_answer = Column(String(200))
    is_correct = Column(Boolean)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TestResult(db.Model):
    """用户测评结果记录表"""
    __tablename__ = 'TestResult'
    id = Column(Integer, autoincrement=True, primary_key=True)
    test_user_id = Column(Integer, nullable=False)
    test_type = Column(String(50), nullable=False)
    test_orientation = Column(String(50), nullable=True)
    score = Column(Float, nullable=False)
    level = Column(String(20))
    acadsoc_level = Column(Integer)
    rate_of_beaten = Column(Float, nullable=False)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class SpeakingTestQuestion(db.Model):
    """口语测评试题库"""
    __tablename__ = 'SpeakingTestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    corpus = Column(String(1000))
    reference_audio_path = Column(String(200))
    analysis = Column(String(300))
    category = Column(String(50))
    acadsoc_level = Column(Integer)
    illustration_pic = Column(String(200))
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class SpeakingTestQuestionAndAnswer(db.Model):
    """用户口语测评试题与答题记录表"""
    __tablename__ = 'SpeakingTestQuestionAndAnswer'
    id = Column(Integer, autoincrement=True, primary_key=True)
    test_user_id = Column(Integer)
    test_user_audio_path = Column(String(200))
    test_question_id = Column(Integer)
    test_result_id = Column(Integer)
    category = Column(String(20))
    is_nonsense = Column(Boolean, default=False)
    accuracy_score = Column(Float, nullable=False)
    standard_score = Column(Float, nullable=False)
    fluency_score = Column(Float, nullable=False)
    integrity_score = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class VocabularyTestQuestion(db.Model):
    """词汇测评试题库"""
    __tablename__ = 'VocabularyTestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    word = Column(String(50))
    part_of_speech = Column(String(50))
    meaning = Column(String(100))
    confusions = Column(String(500))
    rank = Column(Integer)
    audio_path_en = Column(String(300))
    audio_path_us = Column(String(300))
    level = Column(Integer)
    acadsoc_level = Column(Integer)
    grade = Column(String(50))
    unit = Column(String(50))
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class GrammarTestQuestion(db.Model):
    """语法测评试题库"""
    __tablename__ = 'GrammarTestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    question = Column(String(300))
    correct_answer = Column(String(100))
    analysis = Column(String(300))
    confusions = Column(String(200))
    acadsoc_level = Column(Integer)
    illustration_pic = Column(String(200))
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class ListeningTestQuestion(db.Model):
    """听力测评试题库"""
    __tablename__ = 'ListeningTestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    question = Column(String(200))
    correct_answer = Column(String(100))
    analysis = Column(String(300))
    confusions = Column(String(200))
    option_type = Column(String(20))
    audio_path = Column(String(200))
    acadsoc_level = Column(Integer)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class ReadingTestQuestionMaterial(db.Model):
    """阅读测评材料库"""
    __tablename__ = 'ReadingTestQuestionMaterial'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    material = Column(String(2000))
    material_type = Column(String(20))
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class ReadingTestQuestion(db.Model):
    """阅读测评试题库"""
    __tablename__ = 'ReadingTestQuestion'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev_id = Column(Integer, nullable=False)
    material_id = Column(Integer)
    question = Column(String(200))
    correct_answer = Column(String(100))
    analysis = Column(String(300))
    confusions = Column(String(200))
    option_type = Column(String(20))
    acadsoc_level = Column(Integer)
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


class TestQuestionRev(db.Model):
    """测评题库版本表"""
    __tablename__ = 'TestQuestionRev'
    id = Column(Integer, autoincrement=True, primary_key=True)
    question_rev = Column(String(50), nullable=False, unique=True)	 # 字符串，和目前usertestsys文件目录名保持一致，rel_时间
    obsolete = Column(Boolean, default=False)
    create_time = Column(DateTime, server_default=func.now())


db.create_all()
