from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db, User
from schemas import UserSchema

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

@app.get("/")
def read_root():
  return {"message": "Hello World"}

@app.get("/health")
def health_check():
  return {"status": "ok", "message": "Server is running smoothly."}