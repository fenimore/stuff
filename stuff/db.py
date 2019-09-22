from typing import List
import attr
from datetime import datetime
from stuff import Stuff as ApiStuff

from contextlib import contextmanager

from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy import Column, Integer, String, DateTime, Float


Base = declarative_base()


class DBStuff(Base):
    __tablename__ = 'stuff'
    id = Column(Integer, primary_key=True)
    title = Column("title", String, nullable=False)
    url = Column("url", String, nullable=False, unique=True)
    price = Column('price', Integer)
    time = Column('time', DateTime)
    longitude = Column('longititude', Float)
    latitude = Column('latitude', Float)
    image_url = Column('image_url', String)

    @classmethod
    def from_api_model(cls, stuff: ApiStuff):
        return cls(
            title=stuff.title,
            url=stuff.url,
            time=stuff.time,
            price=stuff.price,
            longitude=stuff.coordinates.longitude if stuff.coordinates else None,
            latitude=stuff.coordinates.latitude if stuff.coordinates else None,
            image_url=stuff.image_urls[0] if stuff.image_urls else None,
        )

    def __str__(self):
        return "stuff.db.DBStuff<{} {} {} {}>".format(self.id, self.time, self.title, self.url)


@attr.s
class DBClient:
    _engine: Engine = attr.ib()

    @classmethod
    def new(cls, db_path):
        engine = create_engine(db_path)
        return cls(engine)

    def create_db(self):
        Base.metadata.create_all(self._engine)

    def drop_db(self):
        connection = self._engine.connect()
        Base.metadata.drop_all(connection)
        connection.close()

    def insert_stuff(self, stuff: DBStuff) -> int:
        with self.db_connection() as session:
            session.add(stuff)
            session.commit()
            return stuff.id

    def get_all_stuff(self) -> List[DBStuff]:
        with self.db_connection() as session:
            return session.query(DBStuff).order_by(DBStuff.time.desc()).all()

    def get_stuff_by_id(self, _id) -> DBStuff:
        with self.db_connection() as session:
            return session.query(DBStuff).get(_id)

    def get_stuff_by_url(self, url) -> DBStuff:
        with self.db_connection() as session:
            return session.query(DBStuff).filter_by(url=url).one_or_none()

    @contextmanager
    def db_connection(self):
        try:
            session = Session(self._engine)
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


if __name__ == "__main__":
    client = DBClient.new("sqlite://")  # in memory
    client.drop_db()
    client.create_db()
    stuff_id = client.insert_stuff(
        DBStuff(
            title="My Title",
            url="https://somewhere.com/",
            time=datetime(2019, 4, 20),
            price=0,
            longitude=None,
            latitude=None,
            image_url=None,
        )
    )
    print(client.get_stuff_by_id(stuff_id).price)
    print(client.get_stuff_by_url("https://somewhere.com/").time)
