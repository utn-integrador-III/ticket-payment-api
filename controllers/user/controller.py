from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user.model import UserModel
from utils.server_response import ServerResponse
from utils.message_codes import *
from middleware.auth import auth_required
import qrcode
import io
import base64
import json
import logging

class UserQRController(Resource):
    @auth_required()
    def get(self, current_user=None):
        """
        Genera un código QR con la información del usuario para pagos
        """
        try:
            # Obtener información del usuario
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Crear datos para el QR (solo información necesaria)
            qr_data = {
                'user_id': str(user._id),
                'name': user.name,
                'email': user.email,
                'balance': user.balance,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Convertir a JSON
            qr_json = json.dumps(qr_data)
            
            # Generar código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_json)
            qr.make(fit=True)
            
            # Crear imagen del QR
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return ServerResponse.success(
                data={
                    'qr_code': img_str,
                    'expires_in': 300  # Tiempo de expiración en segundos (5 minutos)
                },
                message_code=QR_GENERATED
            )
            
        except Exception as e:
            logging.exception("Error al generar código QR:")
            return ServerResponse.error(
                "Error al generar el código QR",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @auth_required()
    def get_user_profile(self, current_user=None):
        """
        Obtiene el perfil del usuario actual
        """
        try:
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Obtener métodos de pago (sin información sensible)
            payment_methods = []
            for method in user.payment_methods:
                payment_methods.append({
                    'id': method.get('id'),
                    'card_brand': method.get('card_brand'),
                    'last4': method.get('card_number_last4'),
                    'expiry': method.get('expiry'),
                    'is_default': method.get('is_default', False),
                    'created_at': method.get('created_at')
                })
            
            # Obtener historial de transacciones recientes
            recent_transactions = []
            # Aquí iría la lógica para obtener las transacciones recientes
            
            return ServerResponse.success(
                data={
                    'user': {
                        'id': str(user._id),
                        'name': user.name,
                        'email': user.email,
                        'balance': user.balance,
                        'created_at': user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else user.created_at,
                        'payment_methods': payment_methods,
                        'recent_transactions': recent_transactions
                    }
                }
            )
            
        except Exception as e:
            logging.exception("Error al obtener perfil de usuario:")
            return ServerResponse.error(
                "Error al obtener el perfil de usuario",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
