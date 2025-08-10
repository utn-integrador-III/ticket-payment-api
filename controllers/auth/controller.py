from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from models.user.model import UserModel
from models.auth.schemas import LoginRequest, RegisterRequest, Token
from services.auth_service import AuthService
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Configuración
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
ALGORITHM = "HS256"

# Instancia del servicio de autenticación
auth_service = AuthService(SECRET_KEY, ALGORITHM)

class AuthController:
    @staticmethod
    def register(user_data: RegisterRequest):
        """
        Registrar nuevo usuario
        """
        try:
            # Verificar si el usuario ya existe
            if UserModel.find_by_email(user_data.email):
                raise HTTPException(status_code=400, detail="El usuario ya existe")
            
            # Registrar usuario usando AuthService
            user = auth_service.register_user(user_data)
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
            )
            
            return {
                "message": "Usuario registrado exitosamente",
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": str(user._id),
                    "name": user.name,
                    "email": user.email,
                    "balance": user.balance
                }
            }
            
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def login(user_data: LoginRequest):
        """
        Iniciar sesión
        """
        try:
            # Autenticar usuario
            user = auth_service.authenticate_user(LoginRequest(email=user_data.email, password=user_data.password))
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
            )
            
            if not user:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": str(user._id),
                    "name": user.name,
                    "email": user.email,
                    "balance": user.balance
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Login OAuth2 compatible (para Swagger UI)
        """
        try:
            # Autenticar usuario
            user = auth_service.authenticate_user(LoginRequest(email=form_data.username, password=form_data.password))
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
            )
            
            if not user:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            
            return {
                "access_token": token,
                "token_type": "bearer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en OAuth2 login: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
