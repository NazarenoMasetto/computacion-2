FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
EXPOSE 8000
# exec form: uvicorn es PID 1 y recibe SIGTERM directo de docker stop
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
