from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
from uuid import uuid4
from decouple import config
import logging
import qrcode
import base64
import io
from models.user.model import UserModel
from models.auth.schemas import (
    LoginRequest, RegisterRequest, Token, TokenData, UserProfile,
    PaymentMethod, PaymentMethodIn, TopupRequest, ScanRequest
)
from services.auth_service import AuthService

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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Inicializar servicio de autenticación
auth_service = AuthService(SECRET_KEY, ALGORITHM)

# Rutas de la API
@app.post("/api/register")
async def register_user(payload: RegisterRequest):
    """Registra un nuevo usuario usando UserModel"""
    user = auth_service.register_user(payload)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )

    return {
        "message": "Usuario registrado exitosamente",
        "user_id": str(user._id),
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de pagos con QR"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    login_data = LoginRequest(email=form_data.username, password=form_data.password)
    user = auth_service.authenticate_user(login_data)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Incluir routers de otros módulos
# from routers import users, payments, wallet
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
# app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])

# ---------------------------
# Endpoint de Login
# ---------------------------
@app.post("/api/login")
async def login_user(payload: LoginRequest):
    user = auth_service.authenticate_user(payload)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )

    return {
        "message": "Inicio de sesión exitoso",
        "user_id": str(user._id),
        "access_token": access_token,
        "token_type": "bearer"
    }

# ---------------------------
# Dependencia para obtener usuario actual desde JWT
# ---------------------------

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    return auth_service.get_current_user(token)

# ---------------------------
# Endpoints de usuario
# ---------------------------
@app.get("/api/user/profile", response_model=UserProfile)
async def get_profile(current_user: UserModel = Depends(get_current_user)):
    user_dict = current_user.to_dict()
    return {
        "id": user_dict["id"],
        "name": user_dict["name"],
        "email": user_dict["email"],
        "balance": user_dict["balance"],
        "payment_methods": user_dict["payment_methods"]
    }

@app.get("/api/user/qr")
async def get_user_qr(current_user: UserModel = Depends(get_current_user)):
    img = qrcode.make(str(current_user._id))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    return {"qr_base64": qr_b64}

# ---------------------------
# Endpoints de métodos de pago
# ---------------------------
@app.get("/api/payment/methods")
async def list_payment_methods(current_user: UserModel = Depends(get_current_user)):
    return current_user.payment_methods

@app.post("/api/payment/methods")
async def add_payment_method(method: PaymentMethodIn, current_user: UserModel = Depends(get_current_user)):
    from datetime import datetime
    
    method_dict = method.dict()
    method_dict["id"] = str(uuid4())
    method_dict["created_at"] = datetime.utcnow()
    method_dict["updated_at"] = datetime.utcnow()
    
    # Limpiar métodos vacíos existentes antes de agregar uno nuevo
    current_user.clean_empty_payment_methods()
    
    if current_user.add_payment_method(method_dict):
        return {"message": "Método de pago agregado exitosamente", "payment_method": method_dict}
    else:
        raise HTTPException(status_code=500, detail="Error al agregar método de pago")

@app.delete("/api/payment/methods/{method_id}")
async def delete_payment_method(method_id: str, current_user: UserModel = Depends(get_current_user)):
    if current_user.remove_payment_method(method_id):
        return {"message": "Método de pago eliminado"}
    raise HTTPException(status_code=404, detail="Método de pago no encontrado")

# ---------------------------
# Endpoints de billetera
# ---------------------------
@app.get("/api/wallet")
async def get_wallet_balance(current_user: UserModel = Depends(get_current_user)):
    return {"balance": current_user.balance}

@app.post("/api/wallet/topup")
async def wallet_topup(topup: TopupRequest, current_user: UserModel = Depends(get_current_user)):
    new_balance = current_user.balance + topup.amount
    
    if current_user.update_balance(new_balance):
        return {"message": "Saldo recargado", "balance": current_user.balance}
    else:
        raise HTTPException(status_code=500, detail="Error al actualizar el saldo")

# ---------------------------
# Endpoint de pago por QR
# ---------------------------
@app.post("/api/payment/scan")
async def payment_scan(scan: ScanRequest, current_user: UserModel = Depends(get_current_user)):
    if current_user.balance < scan.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    
    new_balance = current_user.balance - scan.amount
    
    if current_user.update_balance(new_balance):
        return {"message": "Pago realizado", "balance": current_user.balance}
    else:
        raise HTTPException(status_code=500, detail="Error al procesar el pago")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
