from datetime import datetime
from bson import ObjectId
from db.mongodb import db
import logging

class UserModel:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.name = kwargs.get('name', '')
        self.email = kwargs.get('email', '')
        self.password = kwargs.get('password', '')
        self.balance = kwargs.get('balance', 0.0)
        self.payment_methods = kwargs.get('payment_methods', [])
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())

    @classmethod
    def find_by_id(cls, user_id):
        try:
            if not ObjectId.is_valid(user_id):
                return None
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return cls(**user_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar usuario por ID:")
            return None

    @classmethod
    def find_by_email(cls, email):
        try:
            user_data = db.users.find_one({'email': email})
            if user_data:
                return cls(**user_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar usuario por email:")
            return None

    @classmethod
    def create(cls, user_data):
        try:
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            result = db.users.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            return cls(**user_data)
        except Exception as e:
            logging.exception("Error al crear usuario:")
            return None

    def to_dict(self):
        return {
            'id': str(self._id) if self._id else None,
            'name': self.name,
            'email': self.email,
            'balance': self.balance,
            'payment_methods': self.payment_methods,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at
        }

    def remove_payment_method(self, method_id):
        try:
            updated_methods = [m for m in self.payment_methods if m.get('id') != method_id]
            result = db.users.update_one(
                {'_id': self._id},
                {'$set': {'payment_methods': updated_methods, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.payment_methods = updated_methods
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al eliminar método de pago:")
            return False

    def update_password(self, new_password_hash):
        """
        Actualiza la contraseña del usuario
        """
        try:
            result = db.users.update_one(
                {'_id': self._id},
                {'$set': {'password': new_password_hash, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.password = new_password_hash
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar contraseña:")
            return False

    def update_balance(self, new_balance):
        """
        Actualiza el balance del usuario
        """
        try:
            result = db.users.update_one(
                {'_id': self._id},
                {'$set': {'balance': new_balance, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.balance = new_balance
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar balance:")
            return False

    def add_payment_method(self, payment_method):
        """
        Agrega un método de pago al usuario.
        Si existe un método vacío (sin datos), lo reemplaza.
        Si no hay métodos vacíos, agrega uno nuevo.
        """
        try:
            # Verificar si hay métodos de pago vacíos para reemplazar
            empty_method_index = None
            for i, method in enumerate(self.payment_methods):
                # Verificar si el método está vacío (sin card_number o con card_number vacío)
                if not method.get('card_number', '').strip():
                    empty_method_index = i
                    break
            
            if empty_method_index is not None:
                # Reemplazar el método vacío
                old_method = self.payment_methods[empty_method_index]
                self.payment_methods[empty_method_index] = payment_method
            else:
                # No hay métodos vacíos, agregar uno nuevo
                self.payment_methods.append(payment_method)
            
            # Actualizar en la base de datos
            result = db.users.update_one(
                {'_id': self._id},
                {'$set': {'payment_methods': self.payment_methods, 'updated_at': datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                self.updated_at = datetime.utcnow()
                return True
            else:
                # Revertir cambio local si falló la actualización
                if empty_method_index is not None:
                    self.payment_methods[empty_method_index] = old_method
                else:
                    self.payment_methods.pop()
                return False
                
        except Exception as e:
            logging.exception("Error al agregar método de pago:")
            # Revertir cambio local si falló
            if empty_method_index is not None:
                self.payment_methods[empty_method_index] = old_method
            elif payment_method in self.payment_methods:
                self.payment_methods.remove(payment_method)
            return False

    def clean_empty_payment_methods(self):
        """
        Limpia métodos de pago vacíos del usuario
        """
        try:
            # Filtrar métodos que no estén vacíos
            valid_methods = []
            for method in self.payment_methods:
                if method.get('card_number', '').strip():
                    valid_methods.append(method)
            
            if len(valid_methods) != len(self.payment_methods):
                self.payment_methods = valid_methods
                result = db.users.update_one(
                    {'_id': self._id},
                    {'$set': {'payment_methods': self.payment_methods, 'updated_at': datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    self.updated_at = datetime.utcnow()
                    return True
            return True
        except Exception as e:
            logging.exception("Error al limpiar métodos de pago vacíos:")
            return False
