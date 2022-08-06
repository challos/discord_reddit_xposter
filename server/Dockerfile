FROM tiangolo/uwsgi-nginx-flask:python3.8
RUN pip install Flask-SQLAlchemy pyjwt
COPY app/ /app/app/
COPY config.ini uwsgi.ini /app/