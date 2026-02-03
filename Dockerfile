FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# 데이터 저장용 볼륨
VOLUME /data

CMD ["python", "-u", "bot.py"]
