FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY ./data/db.csv ./data/db.csv
COPY ./goodreads_visualizer .

EXPOSE 8501
CMD ["streamlit", "run", "main.py"]
