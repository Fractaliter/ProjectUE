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
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY . /webapp/

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN chmod +x /webapp/entrypoint.sh

EXPOSE 8000
COPY entrypoint.sh /webapp/entrypoint.sh
ENTRYPOINT ["/webapp/entrypoint.sh"]
