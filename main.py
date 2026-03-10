from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from database import get_db, User, DailyEntry
from schemas import UserSchema, UserActivityAggregationResponse

app = FastAPI(
  title="Habit Analytics API",
  description="API which tracks habits and provides analytics."
)

@app.get("/users/{person_id}", response_model=UserSchema)
def get_user_with_entries(person_id: str, db: Session = Depends(get_db)):

  # SQLAlchemy 2.0 select statement to filter by person_id
  stmt = select(User).where(User.person_id == person_id)
  # session executes the statement and selects a single User object or if
  # multiple rows are returned, will produce an error.
  db_user = db.execute(stmt).scalar_one_or_none()

  # explicitely handle the case when user is not found
  if db_user is None:
    raise HTTPException(status_code=404, detail="Error: User not found")
  
  return db_user

@app.get("/users/{person_id}/analytics/activity", response_model=UserActivityAggregationResponse)
def get_user_activity_aggregation(person_id: str, db: Session = Depends(get_db)):
  
  # order of operations: 
  # filter by user (where) -> 
  # group entries by activity (group_by) ->
  # average the groups (func.avg)
  stmt = (
    select(
      DailyEntry.activity_level,
      func.avg(DailyEntry.water_consumption_l).label("average_water_l")
    ).where(DailyEntry.person_id == person_id).group_by(DailyEntry.activity_level)
  )

  results = db.execute(stmt).all()

  # handle edge cases where a user has no entries at a given activity level
  checked_averages = []
  for row in results:
    checked_averages.append({
      "activity_level": row.activity_level,
      "average_water_l": row.average_water_l
    })
  
  # returns an actual dictionary structure so need for ConfigDict in the Schema
  # to allow reading from dot notation objects
  return {
    "person_id": person_id,
    "activity_averages": checked_averages
  }


@app.get("/")
def read_root():
  return {"message": "Hello World"}

@app.get("/health")
def health_check():
  return {"status": "ok", "message": "Server is running smoothly."}