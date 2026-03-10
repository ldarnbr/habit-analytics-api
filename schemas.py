from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List

# Pydantic will enforce the below type hints, preventing SQLaclchemy passing the
# wrong datatype into the columns e.g. string into temperature_c.
class DailyEntrySchema(BaseModel):
  log_id: int
  date: date
  temperature_c: float
  activity_level: str
  water_consumption_l: float

  # ConfigDict allows you to change the default behaviour of pydantic, allowing
  # it to read from attributes (dot notation) instead of the default dict
  # notation. SQLAlchemy returns objects so this is necessary.
  model_config = ConfigDict(from_attributes=True)

class UserSchema(BaseModel):
  person_id: str
  age: int
  gender: str
  city: str

  # Pydantic will look for the entries relationship in SQLAlchemy and extract
  # every entry, run them through the DailyEntrySchema filter and nest them as
  # a list inside the output.
  entries: List[DailyEntrySchema] = []

  model_config = ConfigDict(from_attributes=True)

class ActivityAverageSchema(BaseModel):
  activity_level: str
  average_water_l: float

class UserActivityAggregationResponse(BaseModel):
  person_id: str
  activity_averages: List[ActivityAverageSchema]