import datetime
import os

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL
import jwt

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

ENV = os.getenv("ENV", "production")

app = FastAPI(
    title="LDAP Authentication API with JWT",
    description="FastAPI + OpenLDAP with JWT token generation",
    version="2.0.0",
    docs_url="/docs" if ENV == "development" else None,
    redoc_url="/redoc" if ENV == "development" else None,
    openapi_url="/openapi.json" if ENV == "development" else None,
)

# Middleware para inyectar cabeceras defensivas HTTP
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Restriccion estricta de CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

LDAP_HOST = os.getenv("LDAP_HOST", "openldap")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
JWT_SECRET = os.getenv("JWT_SECRET", "violin_journey_secret_key_2026")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest, x_api_key: str = Header(None, alias="x-api-key")):
    # 1. Validación opcional de x-api-key si se envía
    expected_secret = os.getenv("API_SECRET", os.getenv("API_KEY", None))
    if x_api_key and expected_secret and x_api_key != expected_secret:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: x-api-key invalida",
        )

    # 2. Sanitizacion y prevencion de inyeccion LDAP
    if not re.match(r"^[a-zA-Z0-9_.-]+$", request.username):
        raise HTTPException(
            status_code=400,
            detail="Formato de nombre de usuario invalido (caracteres no permitidos)",
        )

    # 3. Conectar y autenticar contra OpenLDAP
    server = Server(
        LDAP_HOST,
        port=LDAP_PORT,
        get_info=ALL,
    )

    user_dn = (
        f"uid={request.username},"
        f"ou=users,"
        f"{LDAP_BASE_DN}"
    )

    connection = Connection(
        server,
        user=user_dn,
        password=request.password,
        auto_bind=False,
    )

    try:
        if connection.bind():
            now = datetime.datetime.now(datetime.timezone.utc)
            payload = {
                "sub": request.username,
                "username": request.username,
                "role": "musician",
                "iat": int(now.timestamp()),
                "exp": int((now + datetime.timedelta(hours=24)).timestamp()),
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

            return {
                "authenticated": True,
                "token": token,
                "token_type": "Bearer",
                "username": request.username,
                "dn": user_dn,
                "message": "Login exitoso mediante LDAP"
            }

        raise HTTPException(
            status_code=401,
            detail="Credenciales LDAP invalidas (usuario o password incorrecto)",
        )

    finally:
        connection.unbind()

