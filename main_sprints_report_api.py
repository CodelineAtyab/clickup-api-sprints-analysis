import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from src.main_get_sprints_data_app import get_updated_sprints_data


def check_and_reload():
    """Check if reload is needed based on last reload time"""
    try:
        if not os.path.exists('last_reload_epoch_time.txt'):
            # File doesn't exist, trigger immediate reload
            print("No last reload time found. Triggering reload...")
            _perform_reload()
            return
        
        with open('last_reload_epoch_time.txt', 'r') as f:
            last_reload_time = int(f.read().strip())
        
        current_time = int(time.time())
        time_difference = current_time - last_reload_time
        
        # 12 hours in seconds = 12 * 60 * 60 = 43200
        if time_difference >= 43200:
            print(f"Time difference ({time_difference}s) >= 12 hours. Triggering reload...")
            _perform_reload()
    except Exception as e:
        print(f"Error in check_and_reload: {e}")

def _perform_reload():
    """Internal function to perform the actual reload and update timestamp"""
    get_updated_sprints_data()
    
    # Store the epoch time of reload
    epoch_time = int(time.time())
    with open('last_reload_epoch_time.txt', 'w') as f:
        f.write(str(epoch_time))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize scheduler on app startup and cleanup on shutdown"""
    scheduler = BackgroundScheduler()
    # Run check_and_reload every minute
    scheduler.add_job(check_and_reload, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started - checking every minute for reload")
    
    # Run initial check
    check_and_reload()
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    print("Scheduler stopped")

app = FastAPI(title="Sprints Report API", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/reload")
async def reload_sprints_data():
    """Reload the sprints data from the source"""
    try:
        _perform_reload()
        return {"message": "Sprints data reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sprints")
async def get_sprints_data():
    """Return the transformed sprints data as JSON"""
    try:
        with open(os.path.join('fetched_sprints_data', 'transformed_sprints_data.json'), 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sprints data file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON data")

@app.get("/next-reload")
async def get_next_reload_time():
    """Return the time in minutes until the next scheduled reload"""
    try:
        if not os.path.exists('last_reload_epoch_time.txt'):
            return {"minutes_until_reload": 0, "message": "No reload has occurred yet. Reload will happen shortly."}
        
        with open('last_reload_epoch_time.txt', 'r') as f:
            last_reload_time = int(f.read().strip())
        
        current_time = int(time.time())
        time_since_reload = current_time - last_reload_time
        
        # 12 hours in seconds = 43200
        time_until_reload = 43200 - time_since_reload
        
        if time_until_reload <= 0:
            return {"minutes_until_reload": 0, "message": "Reload is due now"}
        
        minutes_until_reload = time_until_reload // 60
        
        return {
            "minutes_until_reload": minutes_until_reload,
            "seconds_until_reload": time_until_reload,
            "last_reload_epoch": last_reload_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def get_report():
    """Serve the HTML report page"""
    return FileResponse("sprints_report.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
