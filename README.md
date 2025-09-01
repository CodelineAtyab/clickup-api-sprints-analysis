# ClickUp API Sprints Analysis

This project analyzes sprints data from ClickUp using their API. It fetches sprint data, processes it, and generates reports in JSON and CSV formats.

## Requirements

- Python 3.7 or higher
- `requests` library
- `python-dotenv` library

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd clickup-api-sprints-analysis
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root and add your ClickUp API credentials:
   ```env
   API_TOKEN=your_api_token
   TEAM_ID=your_team_id
   ```

## Usage

Run the main application:
```bash
python main_app.py
```
