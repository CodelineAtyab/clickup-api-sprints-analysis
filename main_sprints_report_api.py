import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.main_get_sprints_data_app import get_updated_sprints_data


app = FastAPI(title="Sprints Report API")

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
        # Call the function to fetch and transform the sprints data
        get_updated_sprints_data()
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

@app.get("/")
async def get_report():
    """Serve the HTML report page"""
    return FileResponse("sprints_report.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
