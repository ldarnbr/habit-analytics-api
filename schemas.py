from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from typing import List, Dict, Literal, Optional

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
  
  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "date": "2026-03-11",
        "temperature_c": 14.5,
        "activity_level": "Medium",
        "water_consumption_l": 2.5
      }
    }
  )
  
class EntryUpdate(BaseModel):
  temperature_c: Optional[float] = Field(None, ge=-50, le=60)
  activity_level: Optional[Literal['Low', 'Medium', 'High']] = None
  water_consumption_l: Optional[float] = Field(None, ge=0)

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "water_consumption_l": 3.5,
        "activity_level": "High"
      }
    }
  )

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
  model_config = ConfigDict(
    from_attributes=True,
    json_schema_extra={
      "example": {
        "log_id": 1,
        "date": "2026-03-11",
        "temperature_c": 14.5,
        "activity_level": "Medium",
        "water_consumption_l": 2.5
      }
    }
  )

class UserSchema(BaseModel):
  person_id: str
  age: int
  gender: str
  city: str

  # Pydantic will look for the entries relationship in SQLAlchemy and extract
  # every entry, run them through the DailyEntrySchema filter and nest them as
  # a list inside the output.
  entries: List[DailyEntrySchema] = []

  model_config = ConfigDict(
    from_attributes=True,
    json_schema_extra={
      "example": {
        "person_id": "P0001",
        "age": 28,
        "gender": "Female",
        "city": "London",
        "entries": [
          {
            "log_id": 1,
            "date": "2026-03-11",
            "temperature_c": 14.5,
            "activity_level": "Medium",
            "water_consumption_l": 2.5
          }
        ]
      }
    }
  )

class ActivityAverageSchema(BaseModel):
  activity_level: str
  average_water_l: float

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "activity_level": "High",
        "average_water_l": 3.2
      }
    }
  )

class UserActivityAggregationResponse(BaseModel):
  person_id: str
  activity_averages: List[ActivityAverageSchema]

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "person_id": "P0001",
        "activity_averages": [
          {"activity_level": "Low", "average_water_l": 1.5},
          {"activity_level": "Medium", "average_water_l": 2.1},
          {"activity_level": "High", "average_water_l": 3.2}
        ]
      }
    }
  )

class StreakResponse(BaseModel):
  person_id: str
  current_streak: int
  longest_streak: int

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "person_id": "P0001",
        "current_streak": 4,
        "longest_streak": 14
      }
    }
  )

class HeatmapResponse(BaseModel):
  person_id: str
  heatmap_data: Dict[str, float]

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "person_id": "P0001",
        "heatmap_data": {
          "2026-03-01": 2.5,
          "2026-03-02": 1.8,
          "2026-03-03": 3.0
        }
      }
    }
  )

class WeeklyTrendResponse(BaseModel):
  person_id: str
  target_date: date
  current_week_avg: float
  last_week_avg: float
  # percentage change isn't always able to be determined (insufficient data)
  percentage_change: Optional[float] = None
  trend_direction: Literal["up", "down", "flat", "insufficient_data"]

  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "person_id": "P0001",
        "target_date": "2026-03-11",
        "current_week_avg": 2.8,
        "last_week_avg": 2.5,
        "percentage_change": 12.0,
        "trend_direction": "up"
      }
    }
  )