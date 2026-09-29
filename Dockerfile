FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY synthetic_field_prototype.py .
COPY synthetic_generator.py .

CMD ["python", "synthetic_field_prototype.py"]