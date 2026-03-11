from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from database import get_db, User, DailyEntry
from schemas import UserSchema, UserActivityAggregationResponse, StreakResponse, HeatmapResponse, DailyEntrySchema, EntryCreate, EntryUpdate
from datetime import timedelta, date

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
      func.round(func.avg(DailyEntry.water_consumption_l), 2).label("average_water_l")
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

@app.get("/users/{person_id}/analytics/streaks", response_model=StreakResponse)
def get_user_streaks(person_id: str, threshold: float = 2.0, db: Session = Depends(get_db)):
  
  # hard codes threshold water consumption to be considered a streak
  stmt = (
    select(DailyEntry.date).where(DailyEntry.person_id == person_id)
    .where(DailyEntry.water_consumption_l >= threshold)
    .order_by(DailyEntry.date.asc())
  )

  # grab all the rows above the threshold in a list format (scalars)
  above_threshold_dates = db.execute(stmt).scalars().all()

  # trackers
  last_date = None
  current_streak = 0
  longest_streak = 0

  # Note: This loop will differ in production, because as it is, it shows the
  # current streak right up to the last date of entry. The dataset being used
  # is for 2025 only, so current streak would always show 0 in the year 2026.
  # In production it would be more appropriate to compare the last entry to
  # the current date, and if they differ then reset the streak to 0.

  for current_date in above_threshold_dates:
    # start the streak if not already counting
    if last_date is None:
      current_streak = 1
    
    # only increment streak if exactly one day has passed
    elif current_date - last_date == timedelta(days=1):
      current_streak += 1
    
    # reset the streak to 1 if streak gets broken (more than 1 day passed)
    elif (current_date - last_date) > timedelta(days=1):
      current_streak = 1
    
    # keep storing the longest streak counts in a separate if statement
    if current_streak > longest_streak:
      longest_streak = current_streak
    
    # update state for next iteration
    last_date = current_date

  return {
    "person_id": person_id,
    "current_streak": current_streak,
    "longest_streak": longest_streak
  }

@app.get("/users/{person_id}/analytics/heatmap", response_model=HeatmapResponse)
def get_user_heatmap(
  person_id: str, 
  start_date: date = Query(description="Format: YYYY-MM-DD", example="2025-01-01"), 
  end_date: date = Query(description="Format: YYYY-MM-DD", example="2025-12-31"), 
  db: Session = Depends(get_db)
  ):
  
  # includes only entries within the time period specified, for one user
  stmt = (
    select(DailyEntry).where(DailyEntry.person_id == person_id)
    .where(DailyEntry.date >= start_date)
    .where(DailyEntry.date <= end_date)
  )

  entries = db.execute(stmt).scalars().all()

  heatmap = {}
  for entry in entries:
    # key: date object converted to string, value: water consumption in litres
    heatmap[str(entry.date)] = entry.water_consumption_l
  
  return {
    "person_id": person_id,
    "heatmap_data": heatmap
  }

@app.post("/users/{person_id}/entries", response_model=DailyEntrySchema)
def create_entry(
  # FastAPI will look for JSON in the incoming request for the entry_data
  # validates JSON data with pydantic in the EntryCreate schema
  person_id: str, entry_data: EntryCreate, db: Session = Depends(get_db)
):
  
  # check that the user already has entries in the database first
  user = db.execute(select(User).where(User.person_id == person_id)).scalar_one_or_none()
  if user is None:
    raise HTTPException(status_code=404, detail="Error: User not found")
  
  # need to map validated Pydantic data into SQLAlchemy model DailyEntry
  new_entry = DailyEntry(
    person_id=person_id,
    date=entry_data.date,
    temperature_c=entry_data.temperature_c,
    activity_level=entry_data.activity_level,
    water_consumption_l=entry_data.water_consumption_l
  )

  db.add(new_entry)

  try:
    db.commit()
    # database auto increments the log id which new_entry doesn't have yet
    # refresh allows the python variable to catch up and get the log id
    db.refresh(new_entry)
    return new_entry
  except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=400, detail="Entry for this date exists already.")

@app.patch("/users/{person_id}/entries/{entry_date}", response_model=DailyEntrySchema)
def update_entry(
  person_id: str,
  entry_date: date,
  entry_data: EntryUpdate,
  db: Session = Depends(get_db)
):
  
  # find the exact entry from person id and date identifiers
  stmt = select(DailyEntry).where(
    DailyEntry.person_id == person_id, 
    DailyEntry.date == entry_date
  )

  # should return one entry only, else None
  db_entry = db.execute(stmt).scalar_one_or_none()

  if db_entry is None:
    raise HTTPException(status_code=404, detail="Error: User has no entry at this date")

  # get the fields the user sent
  updated_data = entry_data.model_dump(exclude_unset=True)

  # apply the changes to the database object for the attribute the user sent
  for key, value in updated_data.items():
    setattr(db_entry, key, value)

  db.commit()
  db.refresh(db_entry)

  return db_entry

@app.get("/")
def read_root():
  return {"message": "Hello World"}

@app.get("/health")
def health_check():
  return {"status": "ok", "message": "Server is running smoothly."}