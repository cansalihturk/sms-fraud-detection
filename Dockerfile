FROM python:3.12-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY src ./src
COPY .streamlit ./.streamlit

EXPOSE 8000 8501

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
