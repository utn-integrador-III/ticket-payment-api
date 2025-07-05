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
