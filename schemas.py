from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from typing import List, Dict, Literal

class EntryCreate(BaseModel):
  date: date
  # restrict range to sensible temperatures
  temperature_c: float = Field(..., ge=-50, le=60)
  # REFERENCE: 
  # https://stackoverflow.com/questions/74366289/how-to-add-drop-down-menu-to-swagger-ui-autodocs-based-on-basemodel-using-fastap
  activity_level: Literal['Low', 'Medium', 'High']
  # can't log negative water consumption
  water_consumption_l: float = Field(..., ge=0)

  @field_validator('date')
  @classmethod
  def check_date_future(cls, input: date):
    if input > date.today():
      raise ValueError('Entry date cannot be in the future.')
    return input

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

class StreakResponse(BaseModel):
  person_id: str
  current_streak: int
  longest_streak: int

class HeatmapResponse(BaseModel):
  person_id: str
  heatmap_data: Dict[str, float]