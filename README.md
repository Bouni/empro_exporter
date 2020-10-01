## EMpro exporter

A Prometheus exporter for the Phoenix Contact EEM-MA370 energy meter

A possible `docker-compose.yaml` could look like this:

```
version: "3.8"

services:

  prometheus:
    container_name: prometheus
    image: prom/prometheus
    ports:
      - 9090:9090
    volumes:
      - ./prometheus/config.yaml:/etc/prometheus/prometheus.yml
      - ./prometheus/data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-admin-api'
    restart: unless-stopped

  empro-exporter:
    container_name: empro-exporter
    build: git+https://github.com/Bouni/empro_exporter.git
    ports:
      - 9052:9052
    command: ["python", "./empro.py", "192.168.102.2"]
    restart: unless-stopped
```

`192.168.102.2` is the address of the EMpro in this case.
