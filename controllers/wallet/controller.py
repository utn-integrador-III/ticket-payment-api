from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user.model import UserModel
from models.transaction.model import TransactionModel, TransactionType, TransactionStatus
from utils.server_response import ServerResponse
from utils.message_codes import *
from middleware.auth import auth_required
import logging

class WalletController(Resource):
    @auth_required()
    def post(self, current_user=None):
        """
        Recarga el saldo de la billetera del usuario
        """
        try:
            data = request.get_json()
            
            # Validar datos de entrada
            if not data or 'amount' not in data or 'payment_method_id' not in data:
                return ServerResponse.validation_error(message="Monto y método de pago son requeridos")
            
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    raise ValueError("El monto debe ser mayor a cero")
            except (ValueError, TypeError):
                return ServerResponse.validation_error(message="Monto inválido")
            
            # Obtener usuario
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.user_not_found()
            
            # Verificar que el método de pago existe
            payment_method = next((m for m in user.payment_methods if m.get('id') == data['payment_method_id']), None)
            if not payment_method:
                return ServerResponse.payment_method_not_found()
            
            # Procesar la recarga
            transaction, error = TransactionModel.process_topup(
                user_id=user._id,
                amount=amount,
                payment_method_id=payment_method['id'],
                description=f"Recarga de saldo - {payment_method.get('card_brand', '').title()} ••••{payment_method.get('card_number_last4', '')}",
                metadata={
                    'payment_method_type': 'card',
                    'card_brand': payment_method.get('card_brand')
                }
            )
            
            if error:
                return ServerResponse.error(
                    f"Error al procesar la recarga: {error}",
                    status=500,
                    message_code=PAYMENT_FAILED
                )
            
            # Actualizar saldo del usuario
            success, message = user.update_balance(amount)
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
                    'message': 'Recarga exitosa',
                    'transaction_id': str(transaction._id),
                    'amount': amount,
                    'new_balance': user.balance
                },
                message_code=TOPUP_SUCCESSFUL
            )
            
        except Exception as e:
            logging.exception("Error al procesar recarga:")
            return ServerResponse.error(
                "Error al procesar la recarga",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @auth_required()
    def get(self, current_user=None):
        """
        Obtiene el saldo actual del usuario
        """
        try:
            user = UserModel.find_by_id(current_user['_id'])
            if not user:
                return ServerResponse.user_not_found()
            
            return ServerResponse.success(
                data={
                    'balance': user.balance,
                    'currency': 'USD'  # Podría venir de configuración
                }
            )
            
        except Exception as e:
            logging.exception("Error al obtener saldo:")
            return ServerResponse.error(
                "Error al obtener el saldo",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
