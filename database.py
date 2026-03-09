import datetime
from typing import List
from sqlalchemy import ForeignKey, String, Float, Integer, UniqueConstraint, Date, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = "sqlite:///./habit_tracker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# sessionmaker generates identical sessions on demand. The autocommit false
# flag ensures if any API crashes occur, there isnt broken/partial updates to 
# the db. The sessionmaker is bound to the SQLite file using bind=engine.
# This is a class that can be instantiated.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
  # create a new database session
  db = SessionLocal()
  try:
    # yield effectively pauses the function. If it were to be returned,
    # the session would close and the endpoints wouldn't execute.
    yield db
  finally:
    # cleanup only after the endpoint is done. Necessary if theres a crash
    # to guarantee all connections are closed.
    db.close()

class Base(DeclarativeBase):
  pass

class User(Base):
  __tablename__ = "users"
  # expect user.person_id to be a string, and create a column for the data
  person_id: Mapped[str] = mapped_column(String, primary_key=True)
  age: Mapped[int] = mapped_column(Integer)
  gender: Mapped[str] = mapped_column(String)
  city: Mapped[str] = mapped_column(String)

  # one user has many entries, expect a list of entries from the other model
  entries: Mapped[List["DailyEntry"]] = relationship(back_populates="user")

class DailyEntry(Base):
  __tablename__ = "daily_entries"
  log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement\
                                      =True)
  person_id: Mapped[str] = mapped_column(ForeignKey("users.person_id"))
  date: Mapped[datetime.date] = mapped_column(Date)
  temperature_c: Mapped[float] = mapped_column(Float)
  activity_level: Mapped[str] = mapped_column(String)
  water_consumption_l: Mapped[float] = mapped_column(Float)

  # constrains the user to have a maximum of one entry per day
  user: Mapped["User"] = relationship(back_populates="entries")

  __table_args__ = (
    UniqueConstraint('person_id', 'date', name='unique_user_date'),
  )