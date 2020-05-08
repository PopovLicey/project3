from os import abort
from flask import Flask, render_template, redirect, request, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_ngrok import run_with_ngrok
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import flask_login
import datetime
import sqlalchemy
from werkzeug.security import generate_password_hash

SqlAlchemyBase = dec.declarative_base()


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)


class Lesson(SqlAlchemyBase):
    __tablename__ = 'lessons'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    title = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    question_ides = sqlalchemy.Column(sqlalchemy.String)
    popular = sqlalchemy.Column(sqlalchemy.Integer)


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
ses, first = None, True
app = Flask(__name__)
run_with_ngrok(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'Q2WJb4M7Xza0loHh'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)


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


global_init("Project3_1.db")


@app.route('/')
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(f"")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
        return redirect('/main')
    else:
        res = make_response(f"Зарегистрируйтесь или войдите в аккаунт")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
        return redirect('/register')
    return res


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class LessonForm(FlaskForm):
    title = StringField('Название')
    description = TextAreaField('')
    question_ides = StringField('Id заданий')
    popular = 0
    submit = SubmitField('Добавить')


class RegisterForm(FlaskForm):
    name = StringField('Имя')
    surname = StringField('Фамилия')
    prof = SelectField('Вы', choices=[
        ('ученик', 'ученик'),
        ('учитель', 'учитель')])
    password = PasswordField('Пароль')
    email = EmailField('Почта', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@login_manager.user_loader
def load_user(user_id):
    global ses
    ses = create_session()
    return ses.query(User).get(user_id)


class SearchForm(FlaskForm):
    title = StringField('Введите id урока')
    submit = SubmitField('Найти')


@app.route('/main', methods=['GET', 'POST'])
@login_required
def index():
    global ses
    form = SearchForm()
    ses = create_session()
    if form.validate_on_submit():
        id = form.title.data
        lessons = ses.query(Lesson).filter(Lesson.id == id).all()
        if lessons is None:
            return render_template("jobs.html", title='', message='Такого id не существует')
    else:
        lessons = ses.query(Lesson).all()
    return render_template("jobs.html", lessons=lessons, form=form)


@app.route('/add_lesson', methods=['GET', 'POST'])
@login_required
def add_lesson():
    global ses
    user_is_teacher = ses.query(User).filter(User.id == current_user.id).first()
    if user_is_teacher.age == 'учитель':
        form = LessonForm()
        if form.validate_on_submit():
            lesson = Lesson()
            lesson.creator_id = current_user.id
            lesson.title = form.title.data
            lesson.description = form.description.data
            lesson.question_ides = form.question_ides.data
            lesson.popular = 0
            print(lesson.title, form.title, form.title.data)
            ses.add(lesson)
            ses.commit()
            return redirect('/main')
    else:
        return render_template('jobs.html', title='',
                                   message="В доступе отказано")
    return render_template('lessons.html', title='', form=form)


@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/edit_acc', methods=['GET', 'POST'])
def edit_acc():
    global ses
    form = RegisterForm()
    if request.method == "GET":
        ses = create_session()
        user = ses.query(User).filter(User.id == current_user.id).first()
        if user:
            form.name.data = user.name
            form.surname.data = user.surname
            form.prof.data = user.age
            form.password.data = user.hashed_password
            form.email.data = user.email
        else:
            abort(404)
    if form.validate_on_submit():
        ses = create_session()
        user = ses.query(User).filter(User.id == current_user.id).first()
        if user:
            user.name = form.name.data
            user.surname = form.surname.data
            user.age = form.prof.data
            user.set_password(form.password.data)
            user.email = form.email.data
            ses.commit()
            return redirect('/main')
        else:
            abort(404)
    return render_template('register.html', title='Изменение урока', form=form)


@app.route('/go_lesson/<int:id>', methods=['GET', 'POST'])
def go_lesson(id):
    global ses
    user_is_student = ses.query(User).filter(User.id == current_user.id).first()
    if user_is_student.age == 'учитель':
        return render_template('jobs.html', title='',
                               message="В доступе отказано")
    if request.method == 'GET':
        ses = create_session()
        lessons = ses.query(Lesson).filter(Lesson.id == id).first()
        lessons.popular += 1
        ses.commit()
        ql = lessons.question_ides.split(', ')
        list_q = []
        for i in ql:
            quest = ses.query(Question).filter(Question.id == i).first()
            list_q.append([quest, quest.answers.split(', '), quest.correct_ans.split(', ')])
        return render_template('go_test.html', title='Тест', list_q=list_q)
    if request.method == 'POST':
        ses = create_session()
        lessons = ses.query(Lesson).filter(Lesson.id == id).first()
        b = 0
        ql = lessons.question_ides.split(', ')
        for i in ql:
            quest = ses.query(Question).filter(Question.id == i).first()
            if quest.correct_ans == request.form[quest.quest]:
                b += 1
        print(b)
        sas = '<a href="/main" class="btn btn-warning">Вернуться</a>'
        return 'Тест пройден, баллов: ' + str(b) + ' из ' + str(len(ql)) + '\n' + sas


@app.route('/edit_lesson/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_lesson(id):
    global ses
    form = LessonForm()
    if request.method == "GET":
        ses = create_session()
        jobs = ses.query(Lesson).filter(Lesson.id == id and Lesson.creator_id == current_user.id).first()
        if jobs:
            form.title.data = jobs.title
            form.description.data = jobs.description
            form.question_ides.data = jobs.question_ides
        else:
            abort(404)
    if form.validate_on_submit():
        ses = create_session()
        lessons = ses.query(Lesson).filter(Lesson.id == id and Lesson.creator_id == current_user.id).first()
        if lessons:
            lessons.title = form.title.data
            lessons.creator_id = current_user.id
            lessons.question_ides = form.question_ides.data
            lessons.popular = 0
            ses.commit()
            return redirect('/main')
        else:
            abort(404)
    return render_template('lessons.html', title='Изменение урока', form=form)


@app.route('/lesson_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def lesson_delete(id):
    global ses
    ses = create_session()
    lessons = ses.query(Lesson).filter(Lesson.id == id).first()
    if lessons and lessons.creator_id == current_user.id:
        ses.delete(lessons)
        ses.commit()
    else:
        abort(404)
    return redirect('/main')


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
            return redirect("/main")
        return render_template('login.html',
                               message="Что-то пошло не так...",
                               form=form)
    return render_template('login.html', title='Вход', form=form)


class SearchForm2(FlaskForm):
    title = StringField('Введите вопрос в задании')
    submit = SubmitField('Найти')


@app.route('/questions_main', methods=['GET', 'POST'])
@login_required
def index2():
    global ses
    form = SearchForm2()
    ses = create_session()
    if form.validate_on_submit():
        quest = form.title.data
        lessons = ses.query(Question).filter(Question.quest == quest).all()
        if lessons is None:
            return render_template("jobs.html", title='', message='Такого вопроса не существует')
    else:
        lessons = ses.query(Question).all()
    return render_template("quest_main.html", questions=lessons, form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    global ses
    form = RegisterForm()
    if form.validate_on_submit():
        ses = create_session()
        user = User()
        user.name = form.name.data
        user.surname = form.surname.data
        user.age = form.prof.data
        user.set_password(form.password.data)
        user.email = form.email.data
        login_user(user)
        ses.add(user)
        ses.commit()
        return redirect('/main')
    return render_template('register.html', title='Регистрация',
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
        sas = '<a href="/questions_main" class="btn btn-warning">Вернуться на главную</a>'
        return 'Id задания: ' + str(news.id) + ' ' + '<br>' + sas
    return render_template('quest.html', title='Р”РѕР±Р°РІР»РµРЅРёРµ РЅРѕРІРѕСЃС‚Рё',
                           form=form)


@app.route('/logout')
@login_required
def logout():
    global ses
    logout_user()
    return redirect("/login")


if __name__ == '__main__':
    app.run()