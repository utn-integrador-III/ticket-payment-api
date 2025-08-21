from fastapi import Depends
from utils.server_response import ServerResponse
from utils.message_codes import TOPUP_SUCCESSFUL
from models.user.model import UserModel
from models.transaction.model import TransactionModel, TransactionType, TransactionStatus
from models.auth.schemas import TopupRequest
from middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

class WalletController:
    @staticmethod
    def get_balance(current_user: UserModel = Depends(get_current_user)):
        """
        Obtener balance de la billetera
        """
        try:
            return ServerResponse.success(
                data={"balance": current_user.balance},
                message="Balance obtenido exitosamente"
            )
        except Exception as e:
            logger.error(f"Error al obtener balance: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def topup_wallet(topup_data: TopupRequest, current_user: UserModel = Depends(get_current_user)):
        """
        Recargar saldo de la billetera
        """
        try:
            new_balance = current_user.balance + topup_data.amount
            
            if current_user.update_balance(new_balance):
                # Registrar transacción en el historial
                try:
                    transaction = TransactionModel.create(
                        user_id=str(current_user._id),
                        amount=topup_data.amount,
                        transaction_type=TransactionType.TOP_UP,
                        description=f"Recarga de saldo - Método: {topup_data.payment_method_id}",
                        metadata={"payment_method_id": topup_data.payment_method_id}
                    )
                    # Marcar como completada inmediatamente (simulación de pago exitoso)
                    transaction.update_status(TransactionStatus.COMPLETED)
                except Exception as e:
                    # Log error but don't fail the operation
                    logger.warning(f"Error al registrar transacción: {str(e)}")
                
                return ServerResponse.success(
                    data={"balance": current_user.balance},
                    message="Saldo recargado exitosamente",
                    message_code=TOPUP_SUCCESSFUL
                )
            else:
                return ServerResponse.server_error(message="Error al actualizar el saldo")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en recarga de saldo: {str(e)}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    @staticmethod
    def get_transaction_history(
        current_user: UserModel = Depends(get_current_user),
        limit: int = 10,
        offset: int = 0
    ):
        """
        Obtener historial de transacciones del usuario
        """
        try:
            transactions = TransactionModel.find_by_user(
                user_id=str(current_user._id),
                limit=limit,
                offset=offset
            )
            
            # Convertir a diccionarios para la respuesta
            transaction_list = [transaction.to_dict() for transaction in transactions]
            
            return ServerResponse.success(
                data={
                    "transactions": transaction_list,
                    "total_shown": len(transaction_list),
                    "limit": limit,
                    "offset": offset
                },
                message="Historial de transacciones obtenido"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener historial de transacciones: {str(e)}")
            return ServerResponse.server_error(message="Error al obtener historial de transacciones")
