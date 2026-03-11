from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from database import get_db, User, DailyEntry
from schemas import UserSchema, UserActivityAggregationResponse, StreakResponse,\
    HeatmapResponse, DailyEntrySchema, EntryCreate, EntryUpdate, WeeklyTrendResponse
from datetime import timedelta, date

app = FastAPI(
  title="Water Consumption Streak API",
  description="A comprehensive Web Services API for tracking daily hydration",
  version="1.0.0",
  contact={
    "name": "L Brown",
    "email": "sc23ldb@leeds.ac.uk",
  },
  license_info={
    "name": "Apache 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
  },
)

# reusable function to check user exists in the database before actioning
# a request
def verify_user_exists(person_id: str, db: Session = Depends(get_db)):
  user = db.execute(select(User). where(User.person_id == person_id)).scalar_one_or_none()
  
  if user is None:
    raise HTTPException(status_code=404, detail="Error: User not found")
  
  return person_id

@app.get("/users/{person_id}", response_model=UserSchema)
def get_user_with_entries(person_id: str = Depends(verify_user_exists), db: Session = Depends(get_db)):
  """
  Returns all entries for a specified user.
  """
  # SQLAlchemy 2.0 select statement to filter by person_id
  stmt = select(User).where(User.person_id == person_id)
  # session executes the statement and selects a single User object or if
  # multiple rows are returned, will produce an error.
  db_user = db.execute(stmt).scalar_one_or_none()
  
  return db_user

@app.get("/users/{person_id}/analytics/activity", response_model=UserActivityAggregationResponse)
def get_user_activity_aggregation(person_id: str = Depends(verify_user_exists), db: Session = Depends(get_db)):
  """
  Calculates the average water consumption in l for all entries in each tier of 
  reported activity level (Low, Medium, High) for a specified user.
  """
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
def get_user_streaks(person_id: str = Depends(verify_user_exists), threshold: float = 2.0, db: Session = Depends(get_db)):
  """
  Calculates the user's longest hydration streak above the desired threshold.
  Also shows the users ongoing streak.

  **Threshold**: The minimum water consumed in litres to count as a successful day. Defaults to 2.0l.
  """
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
  person_id: str = Depends(verify_user_exists), 
  start_date: date = Query(description="Format: YYYY-MM-DD", example="2025-01-01"), 
  end_date: date = Query(description="Format: YYYY-MM-DD", example="2025-12-31"), 
  db: Session = Depends(get_db)
  ):

  """
  Returns the water consumpion (l) for each entry within the date range specified
  for a specified user.
  """
  
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

@app.get("/users/{person_id}/analytics/trends", response_model=WeeklyTrendResponse)
def get_weekly_trends(
  target_date: date,
  person_id: str = Depends(verify_user_exists),
  db: Session = Depends(get_db)
):
  # week start dates
  start_current = target_date - timedelta(days=7)
  start_last = target_date - timedelta(days=14)

  # one trip to the database to grab all 14 days
  stmt = select(DailyEntry).where(
    DailyEntry.person_id == person_id,
    DailyEntry.date > start_last,
    DailyEntry.date <= target_date
  )
  entries = db.execute(stmt).scalars().all()

  current_week_entries = []
  last_week_entries = []

  for entry in entries:
    if entry.date > start_current:
      current_week_entries.append(entry.water_consumption_l)
    else:
      last_week_entries.append(entry.water_consumption_l)

  # if there is some entries, calculate an average, else set a default avg of 0
  # to avoid divide by zero errors.
  if current_week_entries:
    current_avg = sum(current_week_entries) / len(current_week_entries)
  else:
    current_avg = 0

  if last_week_entries:
    last_avg = sum(last_week_entries) / len(last_week_entries)
  else:
    last_avg = 0

  # calculate percentage change only if there is last weeks avg to compare to
  if last_avg == 0:
    percentage_change = None
    trend_direction = "insufficient_data"
  else:
    percentage_change = round(((current_avg - last_avg) / last_avg) * 100, 2)

    if percentage_change > 0:
      trend_direction = "up"
    elif percentage_change < 0:
      trend_direction = "down"
    else:
      trend_direction = "flat"
  
  return {
    "person_id": person_id,
    "target_date": target_date,
    "current_week_avg": round(current_avg, 2),
    "last_week_avg": round(last_avg, 2),
    "percentage_change": percentage_change,
    "trend_direction": trend_direction
  }

@app.post("/users/{person_id}/entries", response_model=DailyEntrySchema)
def create_entry(
  # FastAPI will look for JSON in the incoming request for the entry_data
  # validates JSON data with pydantic in the EntryCreate schema
  entry_data: EntryCreate, person_id: str = Depends(verify_user_exists), db: Session = Depends(get_db)
):
 
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
  entry_date: date,
  entry_data: EntryUpdate,
  person_id: str = Depends(verify_user_exists),
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
  updated_data = entry_data.model_dump(exclude_unset=True, exclude_none=True)

  # apply the changes to the database object for the attribute the user sent
  for key, value in updated_data.items():
    setattr(db_entry, key, value)

  db.commit()
  db.refresh(db_entry)

  return db_entry

@app.delete("/users/{person_id}/entries/{entry_date}")
def delete_entry(
  entry_date: date,
  person_id: str = Depends(verify_user_exists),
  db: Session = Depends(get_db)
):
  stmt = select(DailyEntry).where(
    DailyEntry.person_id == person_id,
    DailyEntry.date == entry_date
  )
  db_entry = db.execute(stmt).scalar_one_or_none()

  if db_entry is None:
    raise HTTPException(status_code=404, detail="Error: Entry not found for this date.")
  
  db.delete(db_entry)
  db.commit()

  return {"message": f"Entry for {entry_date} by User: {person_id} successfully deleted."}

@app.get("/")
def read_root():
  return {"message": "Hello World"}

@app.get("/health")
def health_check():
  return {"status": "ok", "message": "Server is running smoothly."}