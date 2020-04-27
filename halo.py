# -*- coding: utf-8 -*-
from os import abort
from flask import Flask, render_template, redirect, request, session
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import flask_login
import datetime
import sqlalchemy

SqlAlchemyBase = dec.declarative_base()


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.Integer)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)


class Test(SqlAlchemyBase):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer)
    question_ides = sqlalchemy.Column(sqlalchemy.String)
    popular = sqlalchemy.Column(sqlalchemy.Integer)


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    quest = sqlalchemy.Column(sqlalchemy.String)
    answers = sqlalchemy.Column(sqlalchemy.String)
    type_q = sqlalchemy.Column(sqlalchemy.Integer)
    correct_ans = sqlalchemy.Column(sqlalchemy.String)


__factory = None
ses = None
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=100)


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключено к базе {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


global_init("Project3_2.db")


@app.route('/jobs', methods=['GET', 'POST'])
@login_required
def add_test():
    global ses
    form = TestForm()
    if form.validate_on_submit():
        ses = create_session()
        jobs = Test()
        jobs.name = form.name.data
        jobs.creator_id = form.creator_id.data
        jobs.question_ides = form.question_ides.data
        jobs.popular = 0
        ses.add(jobs)
        ses.commit()
        return redirect('/logout')
    return render_template('news.html', title='Р”РѕР±Р°РІР»РµРЅРёРµ РЅРѕРІРѕСЃС‚Рё',
                           form=form)


class QuestionForm(FlaskForm):
    quest = StringField('Задание')
    answers = StringField('Ответы через запятую и пробел')
    type_q = IntegerField('Тип')
    correct_ans = StringField('Правильный(е) ответ(ы) (через запятую и пробел)')
    submit = SubmitField('Добавить')


@app.route('/add_quest', methods=['GET', 'POST'])
@login_required
def add_quest():
    global ses
    form = QuestionForm()
    if form.validate_on_submit():
        ses = create_session()
        jobs = Question()
        jobs.quest = form.quest.data
        jobs.answers = form.answers.data
        jobs.type_q = form.type_q.data
        jobs.correct_ans = form.correct_ans.data
        ses.add(jobs)
        ses.commit()
        news = ses.query(Question).filter(Question.quest == jobs.quest and Question.answers == jobs.answers and
                                          Question.type_q == jobs.type_q and
                                          Question.correct_ans == jobs.correct_ans).all()
        if news:
            news = news[-1]
        sas = '<a href="/logout" class="btn btn-warning">Вернуться на главную</a>'
        return 'Id задания: ' + str(news.id) + ' ' + '<br>' + sas
    return render_template('quest.html', title='Р”РѕР±Р°РІР»РµРЅРёРµ РЅРѕРІРѕСЃС‚Рё',
                           form=form)


@app.route('/session_test/')
def session_test():
    if 'visits_count' in session:
        session['visits_count'] = session.get('visits_count') + 1
    else:
        session['visits_count'] = 1
    print(session['visits_count'])
    return 1


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class TestForm(FlaskForm):
    name = StringField('Название')
    creator_id = IntegerField('Id Создателя')
    question_ides = StringField('Id заданий')
    popular = 0
    submit = SubmitField('Добавить')


class RegisterForm(FlaskForm):
    name = StringField('Имя')
    surname = StringField('Фамилия')
    age = IntegerField('Возраст')
    password = PasswordField('Пароль')
    email = EmailField('Почта', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@login_manager.user_loader
def load_user(user_id):
    global ses
    ses = create_session()
    return ses.query(User).get(user_id)


@app.route('/logout')
def serdce():
    jobs = sorted(list(ses.query(Test)), key=lambda x: x.popular)[::-1]
    return render_template('jobs.html', jobs=jobs, user=current_user)


@app.route('/go_test/<int:id>', methods=['GET', 'POST'])
def go_test(id):
    global ses
    if request.method == 'GET':
        ses = create_session()
        jobs = ses.query(Test).filter(Test.id == id).first()
        jobs.popular += 1
        ses.commit()
        ql = jobs.question_ides.split(', ')
        list_q = []
        for i in ql:
            quest = ses.query(Question).filter(Question.id == i).first()
            list_q.append([quest, quest.answers.split(', '), quest.correct_ans.split(', ')])
        return render_template('go_test.html', title='Тест', list_q=list_q)
    if request.method == 'POST':
        ses = create_session()
        jobs = ses.query(Test).filter(Test.id == id).first()
        b = 0
        ql = jobs.question_ides.split(', ')
        for i in ql:
            quest = ses.query(Question).filter(Question.id == i).first()
            if quest.correct_ans == request.form[quest.quest]:
                b += 1
        print(b)
        sas = '<a href="/logout" class="btn btn-warning">Вернуться</a>'
        return 'Тест пройден, баллов: ' + str(b) + ' из ' + str(len(ql)) + '<br>' + sas


@app.route('/edit_test/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    global ses
    form = TestForm()
    if request.method == "GET":
        ses = create_session()
        jobs = ses.query(Test).filter(Test.id == id and Test.team_leader == current_user.id).first()
        if jobs:
            form.name.data = jobs.name
            form.creator_id.data = jobs.creator_id
            form.question_ides.data = jobs.question_ides
        else:
            abort(404)
    if form.validate_on_submit():
        ses = create_session()
        jobs = ses.query(Test).filter(Test.id == id and Test.team_leader == current_user.id).first()
        if jobs:
            jobs.name = form.name.data
            jobs.creator_id = form.creator_id.data
            jobs.question_ides = form.question_ides.data
            jobs.popular = 0
            ses.add(jobs)
            ses.commit()
            return redirect('/logout')
        else:
            abort(404)
    return render_template('news.html', title='Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РЅРѕРІРѕСЃС‚Рё', form=form)


@app.route('/test_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    global ses
    ses = create_session()
    news = ses.query(Test).filter(Test.id == id).first()
    if news and news.creator_id == current_user.id:
        ses.delete(news)
        ses.commit()
    else:
        abort(404)
    return redirect('/logout')


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    global ses
    form = LoginForm()
    if form.validate_on_submit():
        ses = create_session()
        user = ses.query(User).filter(User.email == form.email.data and
                                      User.hashed_password == form.password.data).first()
        if user:
            login_user(user, remember=form.remember_me.data)
            return redirect("/logout")
        return render_template('login.html',
                               message="РќРµРїСЂР°РІРёР»СЊРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ",
                               form=form)
    return render_template('login.html', title='РђРІС‚РѕСЂРёР·Р°С†РёСЏ', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    global ses
    form = RegisterForm()
    if form.validate_on_submit():
        ses = create_session()
        user = User()
        user.name = form.name.data
        user.surname = form.surname.data
        user.age = form.age.data
        user.hashed_password = form.password.data
        user.email = form.email.data
        login_user(user)
        ses.add(user)
        ses.commit()
        return redirect('/logout')
    return render_template('register.html', title='Р”РѕР±Р°РІР»РµРЅРёРµ РЅРѕРІРѕСЃС‚Рё',
                           form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')