FROM python:3.9-alpine

RUN apk add --update build-base gcc postgresql-dev

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt
CMD ["python", "-u", "bot.py"]
