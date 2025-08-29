"""
Configuración de rutas usando controllers refactorizados para FastAPI
Este archivo define todas las rutas de la API usando los controllers
"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from models.user.model import UserModel
from models.auth.schemas import (
    LoginRequest, RegisterRequest, Token, UserProfile,
    PaymentMethodIn, TopupRequest, ScanRequest
)
from controllers.auth.controller import AuthController
from controllers.user.controller import UserController
from controllers.payment.controller import PaymentController, PaymentMethodController
from controllers.wallet.controller import WalletController
from middleware.auth import get_current_user

# Router principal
api_router = APIRouter()

# ---------------------------
# Rutas de Autenticación
# ---------------------------
@api_router.post("/register")
async def register(user: RegisterRequest):
    """Registrar nuevo usuario"""
    return AuthController.register(user)

@api_router.post("/login")
async def login(user: LoginRequest):
    """Iniciar sesión"""
    return AuthController.login(user)

@api_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login OAuth2 compatible (para Swagger UI)"""
    return AuthController.oauth2_login(form_data)

# ---------------------------
# Rutas de Usuario
# ---------------------------
@api_router.get("/user/profile", response_model=UserProfile)
async def get_profile(current_user: UserModel = Depends(get_current_user)):
    """Obtener perfil del usuario"""
    return UserController.get_profile(current_user)

@api_router.get("/user/qr")
async def get_user_qr(current_user: UserModel = Depends(get_current_user)):
    """Generar código QR del usuario"""
    return UserController.generate_qr(current_user)

# ---------------------------
# Rutas de Métodos de Pago
# ---------------------------
@api_router.get("/payment/methods")
async def list_payment_methods(current_user: UserModel = Depends(get_current_user)):
    """Obtener métodos de pago del usuario"""
    return PaymentMethodController.get_payment_methods(current_user)

@api_router.post("/payment/methods")
async def add_payment_method(method: PaymentMethodIn, current_user: UserModel = Depends(get_current_user)):
    """Agregar nuevo método de pago"""
    return PaymentMethodController.add_payment_method(method, current_user)

@api_router.delete("/payment/methods/{method_id}")
async def delete_payment_method(method_id: str, current_user: UserModel = Depends(get_current_user)):
    """Eliminar método de pago"""
    return PaymentMethodController.delete_payment_method(method_id, current_user)

# ---------------------------
# Rutas de Pagos
# ---------------------------
@api_router.post("/payment/scan")
async def payment_scan(scan: ScanRequest, current_user: UserModel = Depends(get_current_user)):
    """Procesar pago por escaneo de QR"""
    return PaymentController.scan_payment(scan, current_user)

# ---------------------------
# Rutas de Billetera
# ---------------------------
@api_router.get("/wallet")
async def get_wallet_balance(current_user: UserModel = Depends(get_current_user)):
    """Obtener balance de la billetera"""
    return WalletController.get_balance(current_user)

@api_router.get("/wallet/transactions")
async def get_transaction_history(
    current_user: UserModel = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """Obtener historial de transacciones del usuario"""
    return WalletController.get_transaction_history(current_user, limit, offset)

@api_router.post("/wallet/topup")
async def wallet_topup(topup: TopupRequest, current_user: UserModel = Depends(get_current_user)):
    """Recargar saldo de la billetera"""
    return WalletController.topup_wallet(topup, current_user)
