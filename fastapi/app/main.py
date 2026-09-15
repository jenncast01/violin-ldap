import os

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL

app = FastAPI(
    title="LDAP Authentication API",
    description="Educational FastAPI + OpenLDAP with API Key protection",
    version="1.0.0",
)

# Habilitar CORS para permitir peticiones desde el frontend (http://localhost:8080)
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


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest, x_api_key: str = Header(None, alias="x-api-key")):
    # 1. Validar que la petición incluya la x-api-key correcta (compartida con Front y Back)
    expected_secret = os.getenv("API_SECRET", os.getenv("API_KEY", "LAB-INITIAL-ABC123"))
    if not x_api_key or x_api_key != expected_secret:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: x-api-key invalida o ausente",
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
            return {
                "authenticated": True,
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

