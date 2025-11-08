import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-dev-secret-key-please-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


os.makedirs(app.instance_path, exist_ok=True)


db = SQLAlchemy(app)

#Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy=True)


with app.app_context():
    db.create_all()

#Вспом функция
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None





@app.route('/')
def index():
    current_user = get_current_user()
    messages = Message.query.filter_by(reply_to_id=None).order_by(Message.created_at.desc()).all()
    return render_template('index.html', messages=messages, current_user=current_user)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Имя пользователя и пароль не могут быть пустыми.")
            return redirect(url_for('register'))

        if len(username) < 3:
            flash("Имя пользователя должно содержать не менее 3 символов.")
            return redirect(url_for('register'))

        if len(password) < 6:
            flash("Пароль должен содержать не менее 6 символов.")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Этот никнейм уже занят.")
            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash("Регистрация завершена!")
        return redirect(url_for('index'))

    return render_template('register.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Введите имя пользователя и пароль.")
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Вход выполнен!")
            return redirect(url_for('index'))
        else:
            flash("Неверное имя или пароль.")

    return render_template('login.html')




@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Вы вышли из аккаунта.")
    return redirect(url_for('index'))




@app.route('/message/new', methods=['POST'])
def new_message():
    current_user = get_current_user()
    if not current_user:
        flash("Сначала войдите в аккаунт.")
        return redirect(url_for('login'))

    text = request.form.get('text', '').strip()
    if not text:
        flash("Сообщение не может быть пустым.")
    else:
        message = Message(text=text, user_id=current_user.id)
        db.session.add(message)
        db.session.commit()
        flash("Сообщение отправлено.")

    return redirect(url_for('index'))




@app.route('/message/<int:message_id>/reply', methods=['POST'])
def reply_message(message_id):
    current_user = get_current_user()
    if not current_user:
        flash("Сначала войдите в аккаунт.")
        return redirect(url_for('login'))

    text = request.form.get('text', '').strip()
    if not text:
        flash("Ответ не может быть пустым.")
    else:
        #сущ?
        parent = Message.query.get(message_id)
        if not parent:
            flash("Сообщение для ответа не найдено.")
        else:
            reply = Message(text=text, user_id=current_user.id, reply_to_id=message_id)
            db.session.add(reply)
            db.session.commit()
            flash("Ответ отправлен!")

    return redirect(url_for('index'))




@app.route('/message/<int:message_id>/delete')
def delete_message(message_id):
    current_user = get_current_user()
    if not current_user:
        flash("Сначала войдите в аккаунт.")
        return redirect(url_for('login'))
    message = Message.query.get_or_404(message_id)

    if message.user_id == current_user.id:
        replies = Message.query.filter_by(reply_to_id=message_id).all()
        for reply in replies:
            db.session.delete(reply)
        db.session.delete(message)
        db.session.commit()
        flash("Сообщение удалено.")
    else:
        flash("Вы можете удалять только свои сообщения.")
    return redirect(url_for('index'))






if __name__ == "__main__":
    app.run(debug=True)