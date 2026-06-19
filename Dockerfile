FROM python:3.10

WORKDIR /tinyops

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y docker.io

COPY src ./src
COPY templates ./templates
COPY generated_configs ./generated_configs
COPY blueprint.yaml ./blueprint.yaml

WORKDIR src

CMD ["python", "tinyops.py"]