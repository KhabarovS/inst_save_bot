FROM python:3.12.9-alpine3.21

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV BOT_TOKEN=${BOT_TOKEN}

CMD ["python", "inst_bot.py"]