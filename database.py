from typing import List
from sqlalchemy import ForeignKey, String, Float, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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
  date: Mapped[str] = mapped_column(String)
  temperature_c: Mapped[float] = mapped_column(Float)
  activity_level: Mapped[str] = mapped_column(String)
  water_consumption_l: Mapped[float] = mapped_column(Float)

  # constrains the user to have a maximum of one entry per day
  user: Mapped["User"] = relationship(back_populates="entries")

  __table_args__ = (
    UniqueConstraint('person_id', 'date', name='unique_user_date'),
  )