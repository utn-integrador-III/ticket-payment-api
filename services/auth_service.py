from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from models.user.model import UserModel
from models.auth.schemas import LoginRequest, RegisterRequest
from uuid import uuid4

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

    def authenticate_user(self, login_data: LoginRequest) -> UserModel:
        email = login_data.email.lower().strip()
        user = UserModel.find_by_email(email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        if not self.verify_password(login_data.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        return user

    def register_user(self, register_data: RegisterRequest) -> UserModel:
        email = register_data.email.lower().strip()
        
        # Verificar si el usuario ya existe
        existing_user = UserModel.find_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="El correo electrónico ya está registrado"
            )

        # Preparar datos del usuario
        payment_methods = []
        if register_data.payment_method:
            # Solo agregar si tiene datos válidos
            method_dict = register_data.payment_method
            if (hasattr(method_dict, 'card_number') and method_dict.card_number.strip()) or \
               (isinstance(method_dict, dict) and method_dict.get('card_number', '').strip()):
                # Convertir a dict si es un objeto Pydantic
                if hasattr(register_data.payment_method, 'dict'):
                    method_data = register_data.payment_method.dict()
                else:
                    method_data = register_data.payment_method
                
                # Agregar ID y timestamps
                from datetime import datetime
                method_data["id"] = str(uuid4())
                method_data["created_at"] = datetime.utcnow()
                method_data["updated_at"] = datetime.utcnow()
                
                payment_methods = [method_data]
        
        user_data = {
            "id": str(uuid4()),
            "name": register_data.name.strip(),
            "email": email,
            "password": self.get_password_hash(register_data.password),
            "balance": 0.0,
            "payment_methods": payment_methods
        }

        # Crear usuario usando el modelo
        user = UserModel.create(user_data)
        if not user:
            raise HTTPException(
                status_code=500,
                detail="Error al crear el usuario"
            )
        
        return user

    def get_current_user(self, token: str) -> UserModel:
        email = self.verify_token(token)
        user = UserModel.find_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        return user
