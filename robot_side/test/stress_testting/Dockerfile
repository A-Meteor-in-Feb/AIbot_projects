FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

#RUN apt-get update && apt-get install -y --no-install-recommends wireguard-tools iproute2 iptables openresolv procps && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wg-configs/wgrobot01.conf /etc/wireguard/wg0.conf

COPY mqtt_stressTesting.py start.sh /app/

RUN chmod +x /app/start.sh

ENTRYPOINT ["bash", "/app/start.sh"]
CMD ["--help"]