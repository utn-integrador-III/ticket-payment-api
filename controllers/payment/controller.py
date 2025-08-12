from fastapi import Depends
from utils.server_response import ServerResponse
from utils.message_codes import INSUFFICIENT_BALANCE, PAYMENT_SUCCESSFUL, PAYMENT_METHOD_NOT_FOUND, PAYMENT_METHOD_ADDED
from models.user.model import UserModel
from models.transaction.model import TransactionModel, TransactionType, TransactionStatus
from models.auth.schemas import PaymentMethod, PaymentMethodIn, ScanRequest
from middleware.auth import get_current_user
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class PaymentController:
    @staticmethod
    def scan_payment(scan_data: ScanRequest, current_user: UserModel = Depends(get_current_user)):
        """
        Procesar pago por escaneo de QR
        """
        # Verificar saldo suficiente ANTES de crear la transacción
        if current_user.balance < scan_data.amount:
            # Crear transacción rechazada por saldo insuficiente
            try:
                transaction = TransactionModel.create(
                    user_id=str(current_user._id),
                    amount=-scan_data.amount,
                    transaction_type=TransactionType.PAYMENT,
                    description=f"Pago por QR rechazado - Saldo insuficiente - Código: {scan_data.qr_data}",
                    metadata={"qr_data": scan_data.qr_data, "rejection_reason": "insufficient_balance"}
                )
                transaction.update_status(TransactionStatus.FAILED)
            except Exception as e:
                logger.warning(f"Error al registrar transacción rechazada: {str(e)}")
            
            return ServerResponse.insufficient_balance(required_amount=scan_data.amount, current_balance=current_user.balance)
        
        # Crear transacción y procesar pago
        transaction = None
        try:
            # 1. Crear transacción
            transaction = TransactionModel.create(
                user_id=str(current_user._id),
                amount=-scan_data.amount,  # Negativo porque es un pago
                transaction_type=TransactionType.PAYMENT,
                description=f"Pago por QR - Código: {scan_data.qr_data}",
                metadata={"qr_data": scan_data.qr_data}
            )
            
            # 2. Procesar el pago (actualizar balance)
            new_balance = current_user.balance - scan_data.amount
            if current_user.update_balance(new_balance):
                # 3. Marcar como completada (aprobada)
                transaction.update_status(TransactionStatus.COMPLETED)
                return ServerResponse.success(
                    data={"balance": current_user.balance},
                    message="Pago realizado",
                    message_code=PAYMENT_SUCCESSFUL
                )
            else:
                # 4. Error al actualizar balance - marcar como fallida
                transaction.update_status(TransactionStatus.FAILED)
                return ServerResponse.server_error(message="Error al procesar el pago")
                
        except HTTPException:
            # Re-lanzar HTTPException
            raise
        except Exception as e:
            # Error inesperado - marcar transacción como fallida si existe
            if transaction:
                transaction.update_status(TransactionStatus.FAILED)
            logger.error(f"Error inesperado en pago por QR: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

class PaymentMethodController:
    @staticmethod
    def get_payment_methods(current_user: UserModel = Depends(get_current_user)):
        """
        Obtener métodos de pago del usuario
        """
        try:
            return ServerResponse.success(
                data={
                    "payment_methods": current_user.payment_methods,
                    "count": len(current_user.payment_methods)
                },
                message="Métodos de pago obtenidos"
            )
        except Exception as e:
            logger.error(f"Error al obtener métodos de pago: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def add_payment_method(payment_method: PaymentMethodIn, current_user: UserModel = Depends(get_current_user)):
        """
        Agregar nuevo método de pago
        """
        try:
            # Limpiar métodos de pago vacíos antes de agregar uno nuevo
            current_user.clean_empty_payment_methods()
            
            # Crear método de pago con ID y timestamps
            new_method = PaymentMethod(
                id=str(uuid4()),
                card_holder=payment_method.card_holder,
                card_number=payment_method.card_number,
                expiry=payment_method.expiry,
                cvv=payment_method.cvv,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Agregar método de pago
            if current_user.add_payment_method(new_method.dict()):
                return ServerResponse.success(
                    data={"payment_method": new_method.dict()},
                    message="Método de pago agregado",
                    message_code=PAYMENT_METHOD_ADDED
                )
            else:
                return ServerResponse.server_error(message="Error al agregar método de pago")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al agregar método de pago: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def delete_payment_method(card_holder: str, current_user: UserModel = Depends(get_current_user)):
        """
        Eliminar método de pago por card_holder
        """
        try:
            logger.info(f"Intentando eliminar método de pago para: {card_holder}")
            
            # Usar el método del UserModel para eliminar por card_holder
            if current_user.remove_payment_method_by_card_holder(card_holder):
                logger.info(f"Método de pago eliminado exitosamente para: {card_holder}")
                return ServerResponse.success(
                    message=f"Método de pago de {card_holder} eliminado correctamente"
                )
            else:
                logger.warning(f"Método de pago no encontrado para card_holder: {card_holder}")
                return ServerResponse.payment_method_not_found()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al eliminar método de pago para {card_holder}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
