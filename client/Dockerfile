FROM python:3.10.5-buster
RUN pip install sqlalchemy praw py-cord
COPY ./app/ ./app
WORKDIR /app

CMD ["python", "-u", "main.py"]
