FROM python:3.11-slim

WORKDIR /app

# Instalar Fail2ban y dependencias de red
RUN apt-get update && apt-get install -y --no-install-recommends \
    fail2ban \
    iptables \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Copiar configuración de Fail2ban
COPY jail.local /etc/fail2ban/jail.local
COPY filter-http-flood.conf /etc/fail2ban/filter.d/http-flood.conf
COPY filter-ldap-tls.conf /etc/fail2ban/filter.d/ldap-tls.conf

# Copiar configuración de logs de Uvicorn
COPY log_config.json /app/log_config.json

# Copiar y dar permisos al entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
