FROM python:3.10.5-buster
RUN pip install Flask-SQLAlchemy pyjwt gunicorn
RUN mkdir /data
COPY ./app/ /app/app/
COPY gunicorn_conf.py /app/
WORKDIR /app/

CMD ["gunicorn", "--conf", "gunicorn_conf.py", "--bind", "0.0.0.0:5000", "app.main:app"]
