FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.2"
COPY agents ./agents
RUN pip install --no-cache-dir -e ./agents
COPY api ./api
COPY web ./web
RUN python web/build.py
WORKDIR /app/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
