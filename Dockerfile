FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

ENV TS3_QUERY_PORT="10011"
ENV TS3_SERVER_PORT="9987"
ENV TS3_USERNAME="serveradmin"
ENV TS3_NICKNAME="Discord-Bot"
ENV TS3_VIRTUAL_SERVER_ID="1"

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "python main.py" > /dev/null

CMD ["python", "main.py"]
