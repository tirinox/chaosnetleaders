# set base image (host OS)
FROM python:3.8.1-slim-buster

# set the working directory in the container
WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app/src

# copy the dependencies file to the working directory
COPY requirements.txt .


# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
#COPY src/ .

EXPOSE 5000

# command to run on container start
CMD [ "python", "/app/src/main.py" ]
