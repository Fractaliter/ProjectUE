FROM python:3.12.4

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /webapp

# Tylko podstawowe zależności systemowe (bez MSSQL)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    bash \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Najpierw skrypt entrypoint, potem reszta
COPY entrypoint.sh /webapp/entrypoint.sh

COPY . /webapp/

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000
COPY entrypoint.sh /webapp/entrypoint.sh
ENTRYPOINT ["/webapp/entrypoint.sh"]
