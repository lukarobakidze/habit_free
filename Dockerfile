# use Python 3.11 as the base image
FROM python:3.11-slim

# set working directory
WORKDIR /app

# copy requirements first to leverage Docker cache
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application
COPY . .

# create data directory for SQLite database
RUN mkdir -p /app/data

# expose the port the app runs on
EXPOSE 5002

# command to run the application
CMD ["python", "app.py"] 