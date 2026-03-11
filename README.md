# Hydration Analytics API

## Project Description
A comprehensive RESTful Web Services API build with Python, FastAPI, SQLAlchemy 2.0 and SQLite.
This API provides CRUD operations to manage the full lifecycle of recording daily hydration
logs for individual users. It provides advanced statistical analytics such as weekly hydration trends,
hydration averages corresponding to various user activity levels as well as a streak counter for meeting
custom daily water consumption goals.

The database is populated using the [Daily Water Consumption Dataset](https://www.kaggle.com/datasets/mirzayasirabdullah07/daily-water-consumption-dataset).

## Setup Instructions
1. Clone the repository to your local machine.
```bash
git clone [https://github.com/ldarnbr/habit-analytics-api.git](https://github.com/ldarnbr/habit-analytics-api.git)
```
2. Create a virtual environment to store project dependencies.
```bash
python -m venv venv
```
3. Activate the environment.
```bash
# Windows
venv/Scripts/Activate

# Mac/Linux
source venv/bin/activate
```
4. Install all dependencies.
```bash
pip install -r requirements.txt
```
5. Run the server.
```bash
fastapi dev main.py
```

## Documentation
API documentation generated using Swagger UI is provided in this repository.
Please see the API_Documentation.pdf file located in the documentation directory.