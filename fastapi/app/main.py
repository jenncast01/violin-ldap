import datetime
import os

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL
import jwt

app = FastAPI(
    title="LDAP Authentication API with JWT",
    description="FastAPI + OpenLDAP with JWT token generation",
    version="2.0.0",
)

# Habilitar CORS para permitir peticiones desde cualquier origen (Frontend en Vite o Docker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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

    # 2. Conectar y autenticar contra OpenLDAP
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

