FROM ubuntu:24.04
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y python3-full python3-pip python3-venv && python3 -m venv /venv && /venv/bin/pip install -r requirements.txt
ENTRYPOINT ["/venv/bin/python", "./izzy.py"]
