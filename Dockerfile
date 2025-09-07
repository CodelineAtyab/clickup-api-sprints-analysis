FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  

COPY . .

EXPOSE 8081

CMD ["python", "main_sprints_report_api.py"]