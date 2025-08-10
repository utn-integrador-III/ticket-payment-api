from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from decouple import config
import logging
from models.user.model import UserModel
from models.auth.schemas import (
    LoginRequest, RegisterRequest, Token, UserProfile,
    PaymentMethodIn, TopupRequest, ScanRequest, ChangePasswordRequest
)
from services.auth_service import AuthService
from controllers.auth.controller import AuthController
from controllers.user.controller import UserController
from controllers.payment.controller import PaymentController, PaymentMethodController
from controllers.wallet.controller import WalletController

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
@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de pagos con QR"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return AuthController.oauth2_login(form_data)

# Incluir routers de otros módulos
# from routers import users, payments, wallet
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
# app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])

# ---------------------------
# Endpoint de Login
# ---------------------------

@app.post("/api/register")
async def register(user: RegisterRequest):
    return AuthController.register(user)

@app.post("/api/login")
async def login(user: LoginRequest):
    return AuthController.login(user)

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
    return UserController.get_profile(current_user)

@app.get("/api/user/qr")
async def get_user_qr(current_user: UserModel = Depends(get_current_user)):
    return UserController.generate_qr(current_user)

@app.put("/api/user/change-password")
async def change_password(password_data: ChangePasswordRequest, current_user: UserModel = Depends(get_current_user)):
    return UserController.change_password(password_data, current_user)

# ---------------------------
# Endpoints de métodos de pago
# ---------------------------
@app.get("/api/payment/methods")
async def list_payment_methods(current_user: UserModel = Depends(get_current_user)):
    return PaymentMethodController.get_payment_methods(current_user)

@app.post("/api/payment/methods")
async def add_payment_method(method: PaymentMethodIn, current_user: UserModel = Depends(get_current_user)):
    return PaymentMethodController.add_payment_method(method, current_user)

@app.delete("/api/payment/methods/{card_holder}")
async def delete_payment_method(card_holder: str, current_user: UserModel = Depends(get_current_user)):
    return PaymentMethodController.delete_payment_method(card_holder, current_user)

# ---------------------------
# Endpoints de billetera
# ---------------------------
@app.get("/api/wallet")
async def get_wallet_balance(current_user: UserModel = Depends(get_current_user)):
    return WalletController.get_balance(current_user)

@app.get("/api/wallet/transactions")
async def get_transaction_history(
    current_user: UserModel = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    return WalletController.get_transaction_history(current_user, limit, offset)

@app.post("/api/wallet/topup")
async def wallet_topup(topup: TopupRequest, current_user: UserModel = Depends(get_current_user)):
    return WalletController.topup_wallet(topup, current_user)

# ---------------------------
# Endpoint de pago por QR
# ---------------------------
@app.post("/api/payment/scan")
async def payment_scan(scan: ScanRequest, current_user: UserModel = Depends(get_current_user)):
    return PaymentController.scan_payment(scan, current_user)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
