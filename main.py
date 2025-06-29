from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import uuid4
from pydantic import BaseModel
from decouple import config
import logging
import qrcode
import base64
import io
from db.mongodb import db

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Inicializar FastAPI
app = FastAPI(
    title="Ticket Payment API",
    description="API para sistema de pagos con tarjeta sin contacto mediante códigos QR",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Funciones de utilidad
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Almacén en memoria (solo para pruebas, reemplazar con base de datos real)
USERS_DB: Dict[str, dict] = {}

# Modelos de registro
class PaymentMethod(BaseModel):
    card_number: str
    expiry: str
    cvv: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    payment_method: Optional[PaymentMethod] = None

# Rutas de la API
@app.post("/api/register")
async def register_user(payload: RegisterRequest):
    """Registra un nuevo usuario (memoria y en MongoDB)"""
    email = payload.email.lower().strip()
    if email in USERS_DB:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

    user_id = str(uuid4())
    user_data = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email,
        "password": get_password_hash(payload.password),
        "balance": 0.0,
        "payment_methods": [payload.payment_method.dict()] if payload.payment_method else []
    }
    USERS_DB[email] = user_data

    # Guardar en MongoDB
    db["users"].insert_one(user_data)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)

    return {
        "message": "Usuario registrado exitosamente",
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de pagos con QR"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Aquí irá la lógica de autenticación
    # Por ahora, es un ejemplo básico
    user = {"email": form_data.username}  # Reemplazar con la lógica real
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Incluir routers de otros módulos
# from routers import users, payments, wallet
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
# app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])

# ---------------------------
# Modelo y endpoint de Login
# ---------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
async def login_user(payload: LoginRequest):
    email = payload.email.lower().strip()
    user = USERS_DB.get(email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)

    return {
        "message": "Inicio de sesión exitoso",
        "user_id": user["id"],
        "access_token": access_token,
        "token_type": "bearer"
    }

# ---------------------------
# Dependencia para obtener usuario actual desde JWT
# ---------------------------

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in USERS_DB:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return USERS_DB[email]

# ---------------------------
# Endpoints de usuario
# ---------------------------
class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    balance: float
    payment_methods: list[dict]

@app.get("/api/user/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "balance": current_user["balance"],
        "payment_methods": current_user["payment_methods"]
    }

@app.get("/api/user/qr")
async def get_user_qr(current_user: dict = Depends(get_current_user)):
    img = qrcode.make(current_user["id"])
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    return {"qr_base64": qr_b64}

# ---------------------------
# Endpoints de métodos de pago
# ---------------------------
class PaymentMethodIn(PaymentMethod):
    pass

@app.get("/api/payment/methods")
async def list_payment_methods(current_user: dict = Depends(get_current_user)):
    return current_user["payment_methods"]

@app.post("/api/payment/methods")
async def add_payment_method(method: PaymentMethodIn, current_user: dict = Depends(get_current_user)):
    method_dict = method.dict()
    method_dict["id"] = str(uuid4())
    current_user["payment_methods"].append(method_dict)
    return {"message": "Método de pago agregado", "payment_method": method_dict}

@app.delete("/api/payment/methods/{method_id}")
async def delete_payment_method(method_id: str, current_user: dict = Depends(get_current_user)):
    methods = current_user["payment_methods"]
    for m in methods:
        if m.get("id") == method_id:
            methods.remove(m)
            return {"message": "Método de pago eliminado"}
    raise HTTPException(status_code=404, detail="Método de pago no encontrado")

# ---------------------------
# Endpoints de billetera
# ---------------------------
class TopupRequest(BaseModel):
    amount: float
    payment_method_id: str

@app.get("/api/wallet")
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    return {"balance": current_user["balance"]}

@app.post("/api/wallet/topup")
async def wallet_topup(topup: TopupRequest, current_user: dict = Depends(get_current_user)):
    current_user["balance"] += topup.amount
    return {"message": "Saldo recargado", "balance": current_user["balance"]}

# ---------------------------
# Endpoint de pago por QR
# ---------------------------
class ScanRequest(BaseModel):
    qr_data: str
    amount: float

@app.post("/api/payment/scan")
async def payment_scan(scan: ScanRequest, current_user: dict = Depends(get_current_user)):
    if current_user["balance"] < scan.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    current_user["balance"] -= scan.amount
    return {"message": "Pago realizado", "balance": current_user["balance"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
