from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user.model import UserModel
from models.transaction.model import TransactionModel, TransactionType, TransactionStatus
from utils.server_response import ServerResponse
from utils.message_codes import *
from middleware.auth import auth_required
import logging
import qrcode
import io
import base64

class PaymentController(Resource):
    @auth_required()
    def post(self, current_user=None):
        """
        Procesa el pago de un pasaje escaneando el QR del usuario
        """
        try:
            data = request.get_json()
            
            # Validar datos de entrada
            if not data or 'qr_data' not in data:
                return ServerResponse.error(
                    "Se requiere el código QR del usuario",
                    status=400,
                    message_code=VALIDATION_ERROR
                )
            
            # Aquí iría la lógica para validar el código QR
            # Por ahora, asumimos que el qr_data es el ID del usuario
            user_id = data['qr_data']
            
            # Validar que el usuario exista
            user = UserModel.find_by_id(user_id)
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Monto fijo por pasaje (podría venir en el QR o configurarse)
            ticket_price = 2.50  # Ejemplo: $2.50 por pasaje
            
            # Verificar saldo suficiente
            if user.balance < ticket_price:
                return ServerResponse.error(
                    "Saldo insuficiente",
                    status=402,  # Payment Required
                    message_code=INSUFFICIENT_BALANCE,
                    data={
                        'required_amount': ticket_price,
                        'current_balance': user.balance
                    }
                )
            
            # Procesar el pago
            transaction, error = TransactionModel.process_payment(
                user_id=user._id,
                amount=ticket_price,
                description=f"Pago de pasaje - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                metadata={
                    'ticket_type': 'standard',
                    'validator_id': current_user.get('_id') if current_user else 'system'
                }
            )
            
            if error:
                return ServerResponse.error(
                    f"Error al procesar el pago: {error}",
                    status=500,
                    message_code=PAYMENT_FAILED
                )
            
            # Actualizar saldo del usuario
            success, message = user.update_balance(-ticket_price)
            if not success:
                # Revertir la transacción si no se pudo actualizar el saldo
                transaction.update_status(TransactionStatus.FAILED)
                return ServerResponse.error(
                    "Error al actualizar el saldo",
                    status=500,
                    message_code=PAYMENT_FAILED
                )
            
            return ServerResponse.success(
                data={
                    'message': 'Pago exitoso',
                    'transaction_id': str(transaction._id),
                    'amount': ticket_price,
                    'balance': user.balance
                },
                message_code=PAYMENT_SUCCESSFUL
            )
            
        except Exception as e:
            logging.exception("Error al procesar pago:")
            return ServerResponse.error(
                "Error al procesar el pago",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )

class PaymentMethodController(Resource):
    @auth_required()
    def get(self, current_user=None):
        """
        Obtiene los métodos de pago del usuario
        """
        try:
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Ocultar información sensible de los métodos de pago
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
            
            return ServerResponse.success(
                data={
                    'payment_methods': payment_methods
                }
            )
            
        except Exception as e:
            logging.exception("Error al obtener métodos de pago:")
            return ServerResponse.error(
                "Error al obtener los métodos de pago",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @auth_required()
    def post(self, current_user=None):
        """
        Agrega un nuevo método de pago
        """
        try:
            data = request.get_json()
            
            # Validar datos de la tarjeta
            required_fields = ['card_number', 'expiry', 'cvv']
            for field in required_fields:
                if field not in data:
                    return ServerResponse.error(
                        f"El campo {field} es requerido",
                        status=400,
                        message_code=VALIDATION_ERROR
                    )
            
            # Validar formato de la tarjeta
            if not self._is_valid_card(data):
                return ServerResponse.error(
                    "Datos de tarjeta inválidos",
                    status=400,
                    message_code=INVALID_CARD
                )
            
            # Obtener usuario
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Agregar método de pago
            try:
                payment_method = user.add_payment_method(data)
                
                return ServerResponse.success(
                    data={
                        'message': 'Método de pago agregado exitosamente',
                        'payment_method_id': payment_method['id']
                    },
                    status=201,
                    message_code=PAYMENT_METHOD_ADDED
                )
                
            except ValueError as e:
                return ServerResponse.error(
                    str(e),
                    status=400,
                    message_code=INVALID_CARD_DETAILS
                )
            
        except Exception as e:
            logging.exception("Error al agregar método de pago:")
            return ServerResponse.error(
                "Error al agregar el método de pago",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @auth_required()
    def delete(self, method_id, current_user=None):
        """
        Elimina un método de pago
        """
        try:
            if not method_id:
                return ServerResponse.error(
                    "Se requiere el ID del método de pago",
                    status=400,
                    message_code=VALIDATION_ERROR
                )
            
            # Obtener usuario
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Eliminar método de pago
            try:
                success = user.remove_payment_method(method_id)
                
                if not success:
                    return ServerResponse.error(
                        "No se pudo eliminar el método de pago",
                        status=400,
                        message_code=PAYMENT_METHOD_NOT_FOUND
                    )
                
                return ServerResponse.success(
                    data={'message': 'Método de pago eliminado exitosamente'},
                    message_code=PAYMENT_METHOD_REMOVED
                )
                
            except ValueError as e:
                return ServerResponse.error(
                    str(e),
                    status=400,
                    message_code=VALIDATION_ERROR
                )
            
        except Exception as e:
            logging.exception("Error al eliminar método de pago:")
            return ServerResponse.error(
                "Error al eliminar el método de pago",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _is_valid_card(card_data):
        """Valida los datos básicos de una tarjeta"""
        try:
            # Validar número de tarjeta (solo verificar que sean dígitos y longitud)
            card_number = str(card_data.get('card_number', '')).replace(' ', '')
            if not (13 <= len(card_number) <= 19) or not card_number.isdigit():
                return False
                
            # Validar fecha de expiración (formato MM/YY)
            expiry = card_data.get('expiry', '')
            if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', expiry):
                return False
                
            # Validar CVV (3 o 4 dígitos)
            cvv = str(card_data.get('cvv', ''))
            if not (3 <= len(cvv) <= 4) or not cvv.isdigit():
                return False
                
            return True
            
        except Exception:
            return False
