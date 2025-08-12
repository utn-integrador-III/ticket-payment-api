from fastapi import Depends
from utils.server_response import ServerResponse
from utils.message_codes import USER_NOT_FOUND, PASSWORD_UPDATED, VALIDATION_ERROR, WEAK_PASSWORD
from models.user.model import UserModel
from models.auth.schemas import UserProfile, ChangePasswordRequest
from middleware.auth import get_current_user
from services.auth_service import AuthService
from decouple import config
import qrcode
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# Configuración para AuthService
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key')
ALGORITHM = "HS256"
auth_service = AuthService(SECRET_KEY, ALGORITHM)

class UserController:
    @staticmethod
    def get_profile(current_user: UserModel = Depends(get_current_user)):
        """
        Obtener perfil del usuario actual
        """
        try:
            return ServerResponse.success(
                data={
                    "id": str(current_user._id),
                    "name": current_user.name,
                    "email": current_user.email,
                    "balance": current_user.balance,
                    "payment_methods": current_user.payment_methods or []
                },
                message="Perfil obtenido exitosamente"
            )
        except Exception as e:
            logger.error(f"Error al obtener perfil: {str(e)}")
            return ServerResponse.server_error()
    
    @staticmethod
    def generate_qr(current_user: UserModel = Depends(get_current_user)):
        """
        Generar código QR del usuario para pagos
        """
        try:
            # Crear datos para el QR
            qr_data = str(current_user._id)
            
            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Crear imagen del QR
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return ServerResponse.success(
                data={
                    "qr_code": f"data:image/png;base64,{img_str}",
                    "qr_data": qr_data,
                    "user_id": str(current_user._id),
                    "user_name": current_user.name
                },
                message="QR generado exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al generar QR: {str(e)}")
            return ServerResponse.server_error(message="Error al generar código QR")
    
    @staticmethod
    def change_password(password_data: ChangePasswordRequest, current_user: UserModel = Depends(get_current_user)):
        """
        Cambiar contraseña del usuario
        """
        try:
            # Verificar contraseña actual
            if not auth_service.verify_password(password_data.current_password, current_user.password):
                return ServerResponse.validation_error(message="Contraseña actual incorrecta", message_code=VALIDATION_ERROR)
            
            # Validar nueva contraseña (mínimo 8 caracteres)
            if len(password_data.new_password) < 8:
                return ServerResponse.weak_password()
            
            # Hash de la nueva contraseña
            new_password_hash = auth_service.get_password_hash(password_data.new_password)
            
            # Actualizar contraseña usando el método del modelo
            if current_user.update_password(new_password_hash):
                return ServerResponse.success(
                    data={"updated_at": current_user.updated_at.isoformat()},
                    message="Contraseña actualizada exitosamente",
                    message_code=PASSWORD_UPDATED
                )
            else:
                return ServerResponse.server_error(message="Error al actualizar la contraseña")
                
        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {str(e)}")
            return ServerResponse.server_error()
