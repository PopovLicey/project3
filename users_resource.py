import datetime
import sqlalchemy
from flask import jsonify, Flask
from flask_login import UserMixin
from flask_restful import Resource, Api, abort, reqparse
from sqlalchemy import orm
from sqlalchemy.orm import Session
import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
from sqlalchemy_serializer import SerializerMixin

SqlAlchemyBase = dec.declarative_base()


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.Integer)
    position = sqlalchemy.Column(sqlalchemy.String)
    speciality = sqlalchemy.Column(sqlalchemy.String)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


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


app = Flask(__name__)
api = Api(app)
__factory = None
parser = reqparse.RequestParser()
parser.add_argument('surname', required=True)
parser.add_argument('name', required=True)
parser.add_argument('age', required=True, type=int)
parser.add_argument('position', required=True)
parser.add_argument('speciality', required=True)
parser.add_argument('email', required=True)
parser.add_argument('address', required=True)
parser.add_argument('created_date', required=True)
parser.add_argument('hashed_password', required=True)
global_init("Users.db")


def create_session() -> Session:
    global __factory
    return __factory()


def abort_if_User_not_found(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    print(user)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, User_id):
        abort_if_User_not_found(User_id)
        session = create_session()
        user = session.query(User).get(User_id)
        return jsonify({'User': user.to_dict(
            only=('surname', 'name', 'age', 'position', 'speciality', 'address', 'hashed_password', 'email', 'created_date'))})

    def delete(self, User_id):
        abort_if_User_not_found(User_id)
        session = create_session()
        user = session.query(User).get(User_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = create_session()
        user = session.query(User).all()
        return jsonify({'User': [item.to_dict(
            only=('surname', 'name', 'age', 'position', 'speciality', 'address', 'hashed_password', 'email', 'created_date')) for item in user]})

    def post(self):
        args = parser.parse_args()
        session = create_session()
        user = User(
            title=args['title'],
            content=args['content'],
            user_id=args['user_id'],
            is_published=args['is_published'],
            is_private=args['is_private']
        )
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})


def main():
    global_init("Users.db")
    api.add_resource(UserListResource, '/api/v2/users')
    api.add_resource(UserResource, '/api/v2/users/<int:User_id>')
    app.run()


main()