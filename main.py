from fastapi import FastAPI

app = FastAPI(
  title="Habit Analytics API",
  description="API which tracks habits and provides analytics."
)

@app.get("/")
def read_root():
  return {"message": "Hello World"}

@app.get("/health")
def health_check():
  return {"status": "ok", "message": "Server is running smoothly."}