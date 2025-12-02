FROM python:3.12.9-alpine3.21

WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache ffmpeg && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /root/.config/gallery-dl && cp /app/config.json /root/.config/gallery-dl/config.json

CMD ["python", "inst_bot.py"]