import datetime
import sqlalchemy
from flask import jsonify, Flask
from flask_restful import Resource, Api, abort, reqparse
from sqlalchemy import orm
from sqlalchemy.orm import Session
import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
from sqlalchemy_serializer import SerializerMixin

SqlAlchemyBase = dec.declarative_base()


class Jobs(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'jobs'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    team_leader = sqlalchemy.Column(sqlalchemy.Integer)
    job = sqlalchemy.Column(sqlalchemy.String)
    work_size = sqlalchemy.Column(sqlalchemy.Integer)
    collaborators = sqlalchemy.Column(sqlalchemy.String)
    start_date = sqlalchemy.Column(sqlalchemy.String)
    end_date = sqlalchemy.Column(sqlalchemy.String)
    is_finished = sqlalchemy.Column(sqlalchemy.BOOLEAN)


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
parser.add_argument('team_leader', required=True, type=int)
parser.add_argument('job', required=True)
parser.add_argument('work_size', required=True, type=int)
parser.add_argument('collaborators', required=True)
parser.add_argument('start_date', required=True)
parser.add_argument('end_date', required=True)
parser.add_argument('is_finished', required=True, type=bool)
global_init("Jobs.db")


def create_session() -> Session:
    global __factory
    return __factory()


def abort_if_Jobs_not_found(Jobs_id):
    session = create_session()
    jobs = session.query(Jobs).filter(Jobs.id == Jobs_id).first()
    if not jobs:
        abort(404, message=f"Jobs {Jobs_id} not found")


class JobsResource(Resource):
    def get(self, Jobs_id):
        abort_if_Jobs_not_found(Jobs_id)
        session = create_session()
        jobs = session.query(Jobs).get(Jobs_id)
        return jsonify({'Jobs': jobs.to_dict(
            only=('surname', 'name', 'age', 'position', 'speciality', 'address', 'hashed_password', 'email', 'created_date'))})

    def delete(self, Jobs_id):
        abort_if_Jobs_not_found(Jobs_id)
        session = create_session()
        jobs = session.query(Jobs).get(Jobs_id)
        session.delete(Jobs)
        session.commit()
        return jsonify({'success': 'OK'})


class JobsListResource(Resource):
    def get(self):
        session = create_session()
        jobs = session.query(Jobs).all()
        return jsonify({'Jobs': [item.to_dict(
            only=('surname', 'name', 'age', 'position', 'speciality', 'address', 'hashed_password', 'email', 'created_date')) for item in jobs]})

    def post(self):
        args = parser.parse_args()
        session = create_session()
        jobs = Jobs(
            title=args['title'],
            content=args['content'],
            Jobs_id=args['Jobs_id'],
            is_published=args['is_published'],
            is_private=args['is_private']
        )
        session.add(Jobs)
        session.commit()
        return jsonify({'success': 'OK'})


def main():
    global_init("Jobs.db")
    api.add_resource(JobsListResource, '/api/v2/Jobs')
    api.add_resource(JobsResource, '/api/v2/Jobs/<int:Jobs_id>')
    app.run()


main()