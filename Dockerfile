# to create an image:
# docker build -t windyapi:v1 .

FROM python:3.11.9-bookworm

WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
CMD ["python3", "api.py"]