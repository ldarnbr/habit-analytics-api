import csv
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base, User, DailyEntry

# where to save the file
DATABASE_URL = "sqlite:///./habit_tracker.db"
engine = create_engine(DATABASE_URL, echo=False)

# build the empty tables if they don't already exist
Base.metadata.create_all(bind=engine)

def seed_database(csv_filepath: str):
    """Reads a CSV file and inserts the data into the SQLite database."""
    
    # context manager (with... as) ensures database connection closes when the
    # block finishes. 
    with Session(engine) as session:
        
        # each user has many entries, so it'll attempt to insert the same users
        # repeatedly (causing a crash because of the unique id requirement).
        # Storing users in a set means we can check if a user has already been
        # inserted into the user table.
        seen_user_ids = set()
        
        # open and read the csv file
        with open(csv_filepath, mode='r', encoding='utf-8') as file:
            # csv.DictReader automatically uses the first row as dictionary keys
            reader = csv.DictReader(file)
            
            for row in reader:
                person_id = row['Person_ID']
                
                # Check if we've already created this user in our current run
                if person_id not in seen_user_ids:
                    new_user = User(
                        person_id=person_id,
                        age=int(row['Age']),
                        gender=row['Gender'],
                        city=row['City']
                    )
                    # stores in session not database just yet
                    session.add(new_user)
                    seen_user_ids.add(person_id) # Mark as seen
                
                # string parse time (strptime) reads the string date and 
                # converts it to a native Date object so SQLAlchemy can store it
                log_date = datetime.strptime(row['Date'], "%Y-%m-%d").date()
                
                new_entry = DailyEntry(
                    person_id=person_id,
                    date=log_date,
                    temperature_c=float(row['Temperature_C']),
                    activity_level=row['Activity_Level'],
                    water_consumption_l=float(row['Water_Consumed_Liters'])
                )
                session.add(new_entry)
        
        # We wait until the loop finishes to commit. This batches all data to be
        # inserted into a single transaction. Faster than commiting row by row.
        print("Committing data to the database.")
        session.commit()
        print("Database successfully seeded!")

if __name__ == "__main__":
    csv_file_path = "daily_water_consumption.csv" 
    seed_database(csv_file_path)