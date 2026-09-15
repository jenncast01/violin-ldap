# Docker LDAP + FastAPI Lab

LDAP authentication environment using Docker Compose, OpenLDAP,
phpLDAPadmin, and FastAPI.

This follows the documented osixia Docker Compose configuration for exposing
phpLDAPadmin over HTTP on port 8080.

## Architecture

FastAPI :8000
    |
    | LDAP :389
    v
OpenLDAP :389/:636

phpLDAPadmin :8080
    |
    v
OpenLDAP

## Start

From this directory:

```bash
docker compose down
docker compose pull
docker compose up -d --build
```

If you previously created the containers, the `down` command removes the
containers but preserves the named LDAP volumes.

Do NOT use `docker compose down -v` unless you intentionally want to delete
the LDAP directory data.

## Verify

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

You should see:

```text
phpldapadmin   osixia/phpldapadmin:latest   ...   0.0.0.0:8080->80/tcp
openldap       osixia/openldap:1.5.0         ...   0.0.0.0:389->389/tcp
ldap-api       ldap-docker-api               ...   0.0.0.0:8000->8000/tcp
```

## phpLDAPadmin

Open:

http://localhost:8080

Login DN:

```text
cn=admin,dc=example,dc=com
```

Password:

```text
adminpassword
```

## FastAPI

Open:

http://localhost:8000/docs

Health:

http://localhost:8000/health

## Load sample LDAP users

Copy the LDIF:

```bash
docker cp ldap/users.ldif openldap:/tmp/users.ldif
```

Import it:

```bash
docker exec openldap ldapadd \
  -x \
  -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" \
  -w adminpassword \
  -f /tmp/users.ldif
```

Expected entries:

```text
ou=users
ou=groups
uid=alice
uid=bob
cn=developers
```

## Test LDAP authentication directly

```bash
docker exec openldap ldapwhoami \
  -x \
  -H ldap://localhost \
  -D "uid=alice,ou=users,dc=example,dc=com" \
  -w alice123
```

Expected:

```text
dn:uid=alice,ou=users,dc=example,dc=com
```

## Test FastAPI authentication

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}'
```

Expected response:

```json
{
  "authenticated": true,
  "username": "alice",
  "dn": "uid=alice,ou=users,dc=example,dc=com"
}
```

## LDAP search

```bash
docker exec openldap ldapsearch \
  -x \
  -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" \
  -w adminpassword \
  -b "ou=users,dc=example,dc=com" \
  "(objectClass=inetOrgPerson)"
```

## LDAP structure

```text
dc=example,dc=com
├── ou=users
│   ├── uid=alice
│   └── uid=bob
└── ou=groups
    └── cn=developers
```

## Sample credentials

| Username | Password |
|---|---|
| alice | alice123 |
| bob | bob123 |

LDAP administrator:

```text
DN: cn=admin,dc=example,dc=com
Password: adminpassword
```

These credentials are intentionally simple for the classroom lab.

## Troubleshooting phpLDAPadmin

Check logs:

```bash
docker logs phpldapadmin --tail 100
```

Verify the HTTPS setting:

```bash
docker inspect phpldapadmin   --format '{{range .Config.Env}}{{println .}}{{end}}' | grep PHPLDAPADMIN
```

You should see:

```text
PHPLDAPADMIN_HTTPS=false
PHPLDAPADMIN_LDAP_HOSTS=openldap
```

Verify port mapping:

```bash
docker port phpldapadmin
```

Expected:

```text
80/tcp -> 0.0.0.0:8080
```

## Stop

```bash
docker compose down
```

This preserves LDAP data.

To completely remove the LDAP data:

```bash
docker compose down -v
```

## Security note

This is an educational environment.

LDAP on port 389 is unencrypted and should not be used for production
authentication across an untrusted network. The next exercise can configure
LDAPS on port 636, certificate validation, and packet inspection with
Wireshark.
