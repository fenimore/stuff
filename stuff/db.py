from typing import List
import attr
from datetime import datetime
from stuff.core import Coordinates, Stuff as ApiStuff

from contextlib import contextmanager

from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean


Base = declarative_base()


class DBStuff(Base):
    __tablename__ = 'stuff'
    id = Column(Integer, primary_key=True)
    title = Column("title", String, nullable=False)
    url = Column("url", String, nullable=False, unique=True)
    price = Column('price', Integer)
    time = Column('time', DateTime)
    neighborhood = Column("neighborhood", String)
    longitude = Column('longititude', Float)
    latitude = Column('latitude', Float)
    image_url = Column('image_url', String)
    delivered = Column('delivered', Boolean, default=False)

    @classmethod
    def from_api_model(cls, stuff: ApiStuff):
        return cls(
            id=stuff.id,
            title=stuff.title,
            url=stuff.url,
            time=stuff.time,
            price=stuff.price,
            neighborhood=stuff.neighborhood,
            longitude=stuff.coordinates.longitude if stuff.coordinates else None,
            latitude=stuff.coordinates.latitude if stuff.coordinates else None,
            image_url=stuff.image_urls[0] if stuff.image_urls else None,
            delivered=stuff.delivered,
        )

    def to_api_model(self):
        return ApiStuff(
            id=self.id,
            title=self.title,
            url=self.url,
            time=self.time,
            price=self.price,
            neighborhood=self.neighborhood,
            coordinates=Coordinates(longitude=self.longitude, latitude=self.latitude),
            image_urls=[self.image_url],
            delivered=self.delivered,
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

    def update_stuff(self, update_stuff: DBStuff) -> DBStuff:
        with self.db_connection() as session:
            stuff = session.query(DBStuff).get(update_stuff.id)
            stuff.title = update_stuff.title
            stuff.url = update_stuff.url
            stuff.time = update_stuff.time
            stuff.price = update_stuff.price
            stuff.neighborhood = update_stuff.neighborhood
            stuff.longitude = update_stuff.longitude
            stuff.latitude = update_stuff.latitude
            stuff.image_url = update_stuff.image_url
            stuff.delivered = update_stuff.delivered
            session.commit()
            return update_stuff

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
