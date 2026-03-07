FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && curl -fsSLo /usr/local/bin/supercronic \
    https://github.com/aptible/supercronic/releases/latest/download/supercronic-linux-amd64 \
  && chmod +x /usr/local/bin/supercronic \
  && apt-get purge -y --auto-remove curl \
  && rm -rf /var/lib/apt/lists/*

COPY app /app
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
