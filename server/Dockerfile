FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .
COPY ui/ ./ui/

RUN mkdir -p /data/transfers

EXPOSE 8765

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
