from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.user.model import UserModel
from models.driver.model import DriverModel
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Configuración JWT
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
ALGORITHM = "HS256"

# OAuth2 schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
driver_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="driver/token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    """
    Obtener el usuario actual desde el token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Buscar el usuario por email
    user = UserModel.find_by_email(email)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_driver(token: str = Depends(driver_oauth2_scheme)) -> DriverModel:
    """
    Obtener el chofer actual desde el token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales del chofer",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if email is None or user_type != "driver":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Buscar el chofer por email
    driver = DriverModel.find_by_email(email)
    if driver is None:
        raise credentials_exception
    
    # Verificar que el chofer esté activo
    if not driver.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chofer inactivo"
        )
        
    return driver
