FROM python:3.10.5
RUN pip install Flask-SQLAlchemy pyjwt gunicorn
COPY ./app/ /app/app/
COPY gunicorn_conf.py /app/
COPY config.ini /app/
WORKDIR /app/

CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:80", "app.main:app"]