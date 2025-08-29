from fastapi import Depends
from utils.server_response import ServerResponse
from utils.message_codes import (
    DRIVER_ALREADY_EXISTS, DRIVER_REGISTERED, DRIVER_LOGIN_SUCCESSFUL, 
    INVALID_CREDENTIALS, DRIVER_NOT_FOUND
)
from fastapi.security import OAuth2PasswordRequestForm
from models.driver.model import DriverModel
from models.auth.schemas import DriverLoginRequest, DriverRegisterRequest, Token
from services.auth_service import AuthService
from middleware.auth import get_current_driver
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Configuración
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
ALGORITHM = "HS256"

# Instancia del servicio de autenticación
auth_service = AuthService(SECRET_KEY, ALGORITHM)

class DriverController:
    @staticmethod
    def register(driver_data: DriverRegisterRequest):
        """
        Registrar nuevo chofer
        """
        try:
            # Verificar si el chofer ya existe por email
            if DriverModel.find_by_email(driver_data.email):
                return ServerResponse.error(
                    message="Ya existe un chofer con este email",
                    message_code=DRIVER_ALREADY_EXISTS,
                    status_code=409
                )
            
            # Verificar si ya existe un chofer con esta licencia
            if DriverModel.find_by_license(driver_data.license_number):
                return ServerResponse.error(
                    message="Ya existe un chofer con este número de licencia",
                    message_code=DRIVER_ALREADY_EXISTS,
                    status_code=409
                )
            
            # Hashear la contraseña
            hashed_password = auth_service.get_password_hash(driver_data.password)
            
            # Crear datos del chofer
            driver_dict = {
                "name": driver_data.name,
                "email": driver_data.email,
                "password": hashed_password,
                "license_number": driver_data.license_number,
                "phone": driver_data.phone or "",
                "vehicle_info": {},  # Se puede actualizar después
                "assigned_routes": [],
                "is_active": True
            }
            
            # Crear chofer
            driver = DriverModel.create(driver_dict)
            if not driver:
                return ServerResponse.server_error(message="Error al crear chofer")
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": driver.email, "type": "driver"}, 
                expires_delta=access_token_expires
            )
            
            return ServerResponse.success(
                data={
                    "access_token": token,
                    "token_type": "bearer",
                    "driver": {
                        "id": str(driver._id),
                        "name": driver.name,
                        "email": driver.email,
                        "license_number": driver.license_number,
                        "phone": driver.phone,
                        "vehicle_info": driver.vehicle_info,
                        "assigned_routes": driver.assigned_routes,
                        "is_active": driver.is_active
                    }
                },
                message="Chofer registrado exitosamente",
                message_code=DRIVER_REGISTERED
            )
            
        except Exception as e:
            logger.error(f"Error en registro de chofer: {str(e)}")
            return ServerResponse.server_error()
    
    @staticmethod
    def login(driver_data: DriverLoginRequest):
        """
        Iniciar sesión del chofer
        """
        try:
            # Buscar chofer por email
            driver = DriverModel.find_by_email(driver_data.email)
            if not driver:
                return ServerResponse.unauthorized(
                    message="Credenciales inválidas", 
                    message_code=INVALID_CREDENTIALS
                )
            
            # Verificar contraseña
            if not auth_service.verify_password(driver_data.password, driver.password):
                return ServerResponse.unauthorized(
                    message="Credenciales inválidas", 
                    message_code=INVALID_CREDENTIALS
                )
            
            # Verificar que el chofer esté activo
            if not driver.is_active:
                return ServerResponse.error(
                    message="Chofer inactivo",
                    status_code=403
                )
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": driver.email, "type": "driver"}, 
                expires_delta=access_token_expires
            )
            
            return ServerResponse.success(
                data={
                    "access_token": token,
                    "token_type": "bearer",
                    "driver": {
                        "id": str(driver._id),
                        "name": driver.name,
                        "email": driver.email,
                        "license_number": driver.license_number,
                        "phone": driver.phone,
                        "vehicle_info": driver.vehicle_info,
                        "assigned_routes": driver.assigned_routes,
                        "is_active": driver.is_active
                    }
                },
                message="Inicio de sesión exitoso",
                message_code=DRIVER_LOGIN_SUCCESSFUL
            )
            
        except Exception as e:
            logger.error(f"Error en login de chofer: {str(e)}")
            return ServerResponse.server_error()
    
    @staticmethod
    def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Login OAuth2 compatible para choferes (para Swagger UI)
        """
        try:
            # Buscar chofer por email
            driver = DriverModel.find_by_email(form_data.username)
            if not driver:
                return ServerResponse.unauthorized(
                    message="Credenciales inválidas", 
                    message_code=INVALID_CREDENTIALS
                )
            
            # Verificar contraseña
            if not auth_service.verify_password(form_data.password, driver.password):
                return ServerResponse.unauthorized(
                    message="Credenciales inválidas", 
                    message_code=INVALID_CREDENTIALS
                )
            
            # Verificar que el chofer esté activo
            if not driver.is_active:
                return ServerResponse.error(
                    message="Chofer inactivo",
                    status_code=403
                )
            
            # Crear token de acceso
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30)
            token = auth_service.create_access_token(
                data={"sub": driver.email, "type": "driver"}, 
                expires_delta=access_token_expires
            )
            
            return ServerResponse.success(
                data={
                    "access_token": token,
                    "token_type": "bearer"
                },
                message="Inicio de sesión exitoso",
                message_code=DRIVER_LOGIN_SUCCESSFUL
            )
            
        except Exception as e:
            logger.error(f"Error en OAuth2 login de chofer: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_profile(current_driver: DriverModel = Depends(get_current_driver)):
        """
        Obtener perfil del chofer actual
        """
        try:
            return ServerResponse.success(
                data={
                    "driver": {
                        "id": str(current_driver._id),
                        "name": current_driver.name,
                        "email": current_driver.email,
                        "license_number": current_driver.license_number,
                        "phone": current_driver.phone,
                        "vehicle_info": current_driver.vehicle_info,
                        "assigned_routes": current_driver.assigned_routes,
                        "is_active": current_driver.is_active
                    }
                },
                message="Perfil obtenido exitosamente"
            )
        except Exception as e:
            logger.error(f"Error al obtener perfil de chofer: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def update_vehicle_info(vehicle_info: dict, current_driver: DriverModel = Depends(get_current_driver)):
        """
        Actualizar información del vehículo
        """
        try:
            if current_driver.update_vehicle_info(vehicle_info):
                return ServerResponse.success(
                    data={"vehicle_info": current_driver.vehicle_info},
                    message="Información del vehículo actualizada"
                )
            else:
                return ServerResponse.server_error(message="Error al actualizar información del vehículo")
        except Exception as e:
            logger.error(f"Error al actualizar información del vehículo: {str(e)}")
            return ServerResponse.server_error()
