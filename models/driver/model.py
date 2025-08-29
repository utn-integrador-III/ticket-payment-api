from datetime import datetime
from bson import ObjectId
from db.mongodb import db
import logging

class DriverModel:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.name = kwargs.get('name', '')
        self.email = kwargs.get('email', '')
        self.password = kwargs.get('password', '')
        self.license_number = kwargs.get('license_number', '')
        self.phone = kwargs.get('phone', '')
        self.vehicle_info = kwargs.get('vehicle_info', {})
        self.assigned_routes = kwargs.get('assigned_routes', [])
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())

    @classmethod
    def find_by_id(cls, driver_id):
        try:
            if not ObjectId.is_valid(driver_id):
                return None
            driver_data = db.drivers.find_one({'_id': ObjectId(driver_id)})
            if driver_data:
                return cls(**driver_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar chofer por ID:")
            return None

    @classmethod
    def find_by_email(cls, email):
        try:
            driver_data = db.drivers.find_one({'email': email})
            if driver_data:
                return cls(**driver_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar chofer por email:")
            return None

    @classmethod
    def find_by_license(cls, license_number):
        try:
            driver_data = db.drivers.find_one({'license_number': license_number})
            if driver_data:
                return cls(**driver_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar chofer por licencia:")
            return None

    @classmethod
    def create(cls, driver_data):
        try:
            driver_data['created_at'] = datetime.utcnow()
            driver_data['updated_at'] = datetime.utcnow()
            result = db.drivers.insert_one(driver_data)
            driver_data['_id'] = result.inserted_id
            return cls(**driver_data)
        except Exception as e:
            logging.exception("Error al crear chofer:")
            return None

    def to_dict(self):
        return {
            'id': str(self._id) if self._id else None,
            'name': self.name,
            'email': self.email,
            'license_number': self.license_number,
            'phone': self.phone,
            'vehicle_info': self.vehicle_info,
            'assigned_routes': self.assigned_routes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at
        }

    def update_password(self, new_password_hash):
        """
        Actualiza la contraseña del chofer
        """
        try:
            result = db.drivers.update_one(
                {'_id': self._id},
                {'$set': {'password': new_password_hash, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.password = new_password_hash
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar contraseña del chofer:")
            return False

    def assign_route(self, route_id):
        """
        Asigna una ruta al chofer
        """
        try:
            if route_id not in self.assigned_routes:
                self.assigned_routes.append(route_id)
                result = db.drivers.update_one(
                    {'_id': self._id},
                    {'$set': {'assigned_routes': self.assigned_routes, 'updated_at': datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    self.updated_at = datetime.utcnow()
                    return True
                else:
                    # Revertir cambio local si falló
                    self.assigned_routes.remove(route_id)
                    return False
            return True  # Ya estaba asignada
        except Exception as e:
            logging.exception("Error al asignar ruta al chofer:")
            return False

    def remove_route(self, route_id):
        """
        Remueve una ruta del chofer
        """
        try:
            if route_id in self.assigned_routes:
                self.assigned_routes.remove(route_id)
                result = db.drivers.update_one(
                    {'_id': self._id},
                    {'$set': {'assigned_routes': self.assigned_routes, 'updated_at': datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    self.updated_at = datetime.utcnow()
                    return True
                else:
                    # Revertir cambio local si falló
                    self.assigned_routes.append(route_id)
                    return False
            return True  # Ya no estaba asignada
        except Exception as e:
            logging.exception("Error al remover ruta del chofer:")
            return False

    def update_status(self, is_active):
        """
        Actualiza el estado activo/inactivo del chofer
        """
        try:
            result = db.drivers.update_one(
                {'_id': self._id},
                {'$set': {'is_active': is_active, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.is_active = is_active
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar estado del chofer:")
            return False

    def update_vehicle_info(self, vehicle_info):
        """
        Actualiza la información del vehículo
        """
        try:
            result = db.drivers.update_one(
                {'_id': self._id},
                {'$set': {'vehicle_info': vehicle_info, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.vehicle_info = vehicle_info
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar información del vehículo:")
            return False
