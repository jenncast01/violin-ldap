#!/bin/bash
set -e

# Crear directorios de logs
mkdir -p /var/log/uvicorn /var/log/ldap /var/run/fail2ban

# Limpiar logs anteriores (evita conflictos con symlinks)
rm -f /var/log/uvicorn/access.log /var/log/ldap/connections.log
touch /var/log/uvicorn/access.log /var/log/ldap/connections.log

# Limpiar estado anterior de fail2ban
rm -f /var/run/fail2ban/fail2ban.sock /var/run/fail2ban/fail2ban.pid
touch /var/log/fail2ban.log

# Arrancar Uvicorn en background con access log a archivo
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --access-log \
  --log-level info \
  --log-config /app/log_config.json &

sleep 2

# Arrancar Fail2ban (protege HTTP puerto 8000 + LDAP TLS puerto 636)
fail2ban-client -x start

echo "[ldap-api] Uvicorn + Fail2ban corriendo exitosamente."
exec tail -F /var/log/fail2ban.log
