from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json
import os

app = FastAPI(title="Sprints Report API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/sprints")
async def get_sprints_data():
    """Return the transformed sprints data as JSON"""
    try:
        with open(os.path.join('output', 'transformed_sprints_data.json'), 'r') as file:
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
