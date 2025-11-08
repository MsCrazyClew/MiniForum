from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

    messages = db.relationship('Message', backref='user')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #Кто
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #Отв на какое сообщение
    reply_to_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    #Связь для отв
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]))

