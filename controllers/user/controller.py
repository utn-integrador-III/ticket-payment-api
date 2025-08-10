from fastapi import HTTPException, Depends
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
            return {
                "id": str(current_user._id),
                "name": current_user.name,
                "email": current_user.email,
                "balance": current_user.balance,
                "payment_methods": current_user.payment_methods or []
            }
        except Exception as e:
            logger.error(f"Error al obtener perfil: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
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
            
            return {
                "qr_code": f"data:image/png;base64,{img_str}",
                "qr_data": qr_data,
                "user_id": str(current_user._id),
                "user_name": current_user.name
            }
            
        except Exception as e:
            logger.error(f"Error al generar QR: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al generar código QR")
    
    @staticmethod
    def change_password(password_data: ChangePasswordRequest, current_user: UserModel = Depends(get_current_user)):
        """
        Cambiar contraseña del usuario
        """
        try:
            # Verificar contraseña actual
            if not auth_service.verify_password(password_data.current_password, current_user.password):
                raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
            
            # Validar nueva contraseña (mínimo 8 caracteres)
            if len(password_data.new_password) < 8:
                raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 8 caracteres")
            
            # Hash de la nueva contraseña
            new_password_hash = auth_service.get_password_hash(password_data.new_password)
            
            # Actualizar contraseña usando el método del modelo
            if current_user.update_password(new_password_hash):
                return {
                    "message": "Contraseña actualizada exitosamente",
                    "updated_at": current_user.updated_at.isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="Error al actualizar la contraseña")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
