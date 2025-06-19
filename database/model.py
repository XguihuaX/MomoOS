# backend/models.py
from database.init import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum as SQLAEnum
import enum
from sqlalchemy.dialects.mysql import TEXT




#  memory 表

class Memory_role(str,enum.Enum):
    user = 'user'
    ststem = 'system'

class Memory_type(str,enum.Enum):
    fact ='fact'
    instruction = 'instruction'
    emotion = 'emotion'
    activity = 'activity'
    daily = 'daily'

class Memory(db.Model):
    __tablename__ = "memory"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), db.ForeignKey("users.user_id"), nullable=False)
    role = db.Column(db.Enum(Memory_role), nullable=False)
    type = db.Column(db.Enum(Memory_type), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



#####--------personality ---------######


class personality_type(str,enum.Enum):
    personality = "personality"
    preference = "preference"

class personality(db.Model):
    __tablename__ = 'personality'
    user_id = db.Column(db.String(64), db.ForeignKey('users.user_id'), primary_key=True)
    type = db.Column(SQLAEnum(personality_type), primary_key=True)
    tag = db.Column(db.String(255), primary_key=True)
    content = db.Column(db.Text, nullable=False)  # 建议非空




# todos 表
class OwnerTypeEnum(str, enum.Enum):
    agent = 'agent'
    alarm = 'alarm'
    schedule = 'schedule'

class StatusEnum(str, enum.Enum):
    pending = 'pending'
    completed = 'completed'
    failed = 'failed'
    multiple = 'multiple'


class Todo(db.Model):
    __tablename__ = 'todos'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci'
    }
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), db.ForeignKey('users.user_id'), nullable=False)  #  用户隔离
    owner_type = db.Column(SQLAEnum(OwnerTypeEnum), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(TEXT(charset='utf8mb4'), nullable=True)
    due_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(SQLAEnum(StatusEnum), default=StatusEnum.pending, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)



#user表
class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(64), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)