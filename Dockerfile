# pull official base image
FROM python

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /app/

CMD ["gunicorn", "--chdir", "/app", "server:app", "-w", "2", "--threads", "2", "-b", "0.0.0.0:80"]
EXPOSE 80