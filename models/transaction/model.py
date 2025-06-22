from datetime import datetime
from bson import ObjectId
from enum import Enum
from db.mongodb import db
import logging

class TransactionType(Enum):
    PAYMENT = "payment"
    TOP_UP = "top_up"
    REFUND = "refund"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class TransactionModel:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.user_id = kwargs.get('user_id')
        self.amount = kwargs.get('amount', 0.0)
        self.transaction_type = kwargs.get('transaction_type')
        self.status = kwargs.get('status', TransactionStatus.PENDING.value)
        self.description = kwargs.get('description', '')
        self.metadata = kwargs.get('metadata', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    def to_dict(self):
        return {
            'id': str(self._id) if self._id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def create(cls, user_id, amount, transaction_type, description='', metadata=None):
        """
        Crea una nueva transacción
        """
        try:
            if not ObjectId.is_valid(user_id):
                raise ValueError("ID de usuario inválido")
                
            transaction_data = {
                'user_id': ObjectId(user_id),
                'amount': float(amount),
                'transaction_type': transaction_type.value if hasattr(transaction_type, 'value') else transaction_type,
                'status': TransactionStatus.PENDING.value,
                'description': description,
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = db.transactions.insert_one(transaction_data)
            transaction_data['_id'] = result.inserted_id
            
            return cls(**transaction_data)
            
        except Exception as e:
            logging.exception("Error al crear transacción:")
            raise e
    
    @classmethod
    def find_by_id(cls, transaction_id):
        """
        Busca una transacción por su ID
        """
        try:
            if not ObjectId.is_valid(transaction_id):
                return None
                
            transaction_data = db.transactions.find_one({'_id': ObjectId(transaction_id)})
            if transaction_data:
                return cls(**transaction_data)
            return None
            
        except Exception as e:
            logging.exception("Error al buscar transacción por ID:")
            return None
    
    @classmethod
    def find_by_user(cls, user_id, limit=10, offset=0):
        """
        Obtiene el historial de transacciones de un usuario
        """
        try:
            if not ObjectId.is_valid(user_id):
                return []
                
            cursor = db.transactions.find({'user_id': ObjectId(user_id)}) \
                                     .sort('created_at', -1) \
                                     .skip(offset) \
                                     .limit(limit)
            
            return [cls(**t) for t in cursor]
            
        except Exception as e:
            logging.exception("Error al buscar transacciones por usuario:")
            return []
    
    def update_status(self, new_status):
        """
        Actualiza el estado de una transacción
        """
        try:
            if not self._id:
                raise ValueError("La transacción no tiene un ID válido")
                
            result = db.transactions.update_one(
                {'_id': self._id},
                {'$set': {
                    'status': new_status.value if hasattr(new_status, 'value') else new_status,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                self.status = new_status.value if hasattr(new_status, 'value') else new_status
                self.updated_at = datetime.utcnow()
                return True
                
            return False
            
        except Exception as e:
            logging.exception("Error al actualizar estado de transacción:")
            return False
    
    @classmethod
    def process_payment(cls, user_id, amount, description='', metadata=None):
        """
        Procesa un pago (cargo al usuario)
        """
        try:
            # Crear transacción pendiente
            transaction = cls.create(
                user_id=user_id,
                amount=-abs(float(amount)),  # Aseguramos que sea negativo
                transaction_type=TransactionType.PAYMENT,
                description=description,
                metadata=metadata or {}
            )
            
            # Aquí iría la lógica para procesar el pago con la pasarela de pago
            # Por ahora, simulamos un pago exitoso
            
            # Actualizar estado a completado
            transaction.update_status(TransactionStatus.COMPLETED)
            
            return transaction, None
            
        except Exception as e:
            logging.exception("Error al procesar pago:")
            if 'transaction' in locals():
                transaction.update_status(TransactionStatus.FAILED)
            return None, str(e)
    
    @classmethod
    def process_topup(cls, user_id, amount, payment_method_id, description='', metadata=None):
        """
        Procesa una recarga de saldo
        """
        try:
            # Crear transacción pendiente
            transaction = cls.create(
                user_id=user_id,
                amount=abs(float(amount)),  # Aseguramos que sea positivo
                transaction_type=TransactionType.TOP_UP,
                description=description,
                metadata={
                    'payment_method_id': payment_method_id,
                    **(metadata or {})
                }
            )
            
            # Aquí iría la lógica para procesar el pago con la pasarela de pago
            # Por ahora, simulamos un pago exitoso
            
            # Actualizar estado a completado
            transaction.update_status(TransactionStatus.COMPLETED)
            
            return transaction, None
            
        except Exception as e:
            logging.exception("Error al procesar recarga:")
            if 'transaction' in locals():
                transaction.update_status(TransactionStatus.FAILED)
            return None, str(e)
