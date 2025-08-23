from datetime import datetime
from bson import ObjectId
from db.mongodb import db
import logging

class RouteModel:
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.name = kwargs.get('name', '')
        self.code = kwargs.get('code', '')  # Código único de la ruta
        self.description = kwargs.get('description', '')
        self.origin = kwargs.get('origin', '')
        self.destination = kwargs.get('destination', '')
        self.stops = kwargs.get('stops', [])  # Lista de paradas
        self.fare_amount = kwargs.get('fare_amount', 0.0)  # Monto del pasaje
        self.distance_km = kwargs.get('distance_km', 0.0)
        self.estimated_duration = kwargs.get('estimated_duration', 0)  # En minutos
        self.assigned_drivers = kwargs.get('assigned_drivers', [])  # IDs de choferes asignados
        self.is_active = kwargs.get('is_active', True)
        self.schedule = kwargs.get('schedule', {})  # Horarios de operación
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())

    @classmethod
    def find_by_id(cls, route_id):
        try:
            if not ObjectId.is_valid(route_id):
                return None
            route_data = db.routes.find_one({'_id': ObjectId(route_id)})
            if route_data:
                return cls(**route_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar ruta por ID:")
            return None

    @classmethod
    def find_by_code(cls, code):
        try:
            route_data = db.routes.find_one({'code': code})
            if route_data:
                return cls(**route_data)
            return None
        except Exception as e:
            logging.exception("Error al buscar ruta por código:")
            return None

    @classmethod
    def find_by_driver(cls, driver_id):
        """
        Encuentra todas las rutas asignadas a un chofer
        """
        try:
            routes_data = db.routes.find({'assigned_drivers': driver_id})
            routes = []
            for route_data in routes_data:
                routes.append(cls(**route_data))
            return routes
        except Exception as e:
            logging.exception("Error al buscar rutas por chofer:")
            return []

    @classmethod
    def get_all_active(cls):
        """
        Obtiene todas las rutas activas
        """
        try:
            routes_data = db.routes.find({'is_active': True})
            routes = []
            for route_data in routes_data:
                routes.append(cls(**route_data))
            return routes
        except Exception as e:
            logging.exception("Error al obtener rutas activas:")
            return []

    @classmethod
    def create(cls, route_data):
        try:
            route_data['created_at'] = datetime.utcnow()
            route_data['updated_at'] = datetime.utcnow()
            result = db.routes.insert_one(route_data)
            route_data['_id'] = result.inserted_id
            return cls(**route_data)
        except Exception as e:
            logging.exception("Error al crear ruta:")
            return None

    def to_dict(self):
        return {
            'id': str(self._id) if self._id else None,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'origin': self.origin,
            'destination': self.destination,
            'stops': self.stops,
            'fare_amount': self.fare_amount,
            'distance_km': self.distance_km,
            'estimated_duration': self.estimated_duration,
            'assigned_drivers': self.assigned_drivers,
            'is_active': self.is_active,
            'schedule': self.schedule,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at
        }

    def assign_driver(self, driver_id):
        """
        Asigna un chofer a la ruta
        """
        try:
            if driver_id not in self.assigned_drivers:
                self.assigned_drivers.append(driver_id)
                result = db.routes.update_one(
                    {'_id': self._id},
                    {'$set': {'assigned_drivers': self.assigned_drivers, 'updated_at': datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    self.updated_at = datetime.utcnow()
                    return True
                else:
                    # Revertir cambio local si falló
                    self.assigned_drivers.remove(driver_id)
                    return False
            return True  # Ya estaba asignado
        except Exception as e:
            logging.exception("Error al asignar chofer a la ruta:")
            return False

    def remove_driver(self, driver_id):
        """
        Remueve un chofer de la ruta
        """
        try:
            if driver_id in self.assigned_drivers:
                self.assigned_drivers.remove(driver_id)
                result = db.routes.update_one(
                    {'_id': self._id},
                    {'$set': {'assigned_drivers': self.assigned_drivers, 'updated_at': datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    self.updated_at = datetime.utcnow()
                    return True
                else:
                    # Revertir cambio local si falló
                    self.assigned_drivers.append(driver_id)
                    return False
            return True  # Ya no estaba asignado
        except Exception as e:
            logging.exception("Error al remover chofer de la ruta:")
            return False

    def update_fare(self, new_fare):
        """
        Actualiza el monto del pasaje
        """
        try:
            result = db.routes.update_one(
                {'_id': self._id},
                {'$set': {'fare_amount': new_fare, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.fare_amount = new_fare
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar tarifa de la ruta:")
            return False

    def update_status(self, is_active):
        """
        Actualiza el estado activo/inactivo de la ruta
        """
        try:
            result = db.routes.update_one(
                {'_id': self._id},
                {'$set': {'is_active': is_active, 'updated_at': datetime.utcnow()}}
            )
            if result.modified_count > 0:
                self.is_active = is_active
                self.updated_at = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar estado de la ruta:")
            return False

    def update_route_info(self, route_data):
        """
        Actualiza información general de la ruta
        """
        try:
            update_data = {
                'name': route_data.get('name', self.name),
                'description': route_data.get('description', self.description),
                'origin': route_data.get('origin', self.origin),
                'destination': route_data.get('destination', self.destination),
                'stops': route_data.get('stops', self.stops),
                'distance_km': route_data.get('distance_km', self.distance_km),
                'estimated_duration': route_data.get('estimated_duration', self.estimated_duration),
                'schedule': route_data.get('schedule', self.schedule),
                'updated_at': datetime.utcnow()
            }
            
            result = db.routes.update_one(
                {'_id': self._id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                # Actualizar atributos locales
                for key, value in update_data.items():
                    if key != 'updated_at':
                        setattr(self, key, value)
                self.updated_at = update_data['updated_at']
                return True
            return False
        except Exception as e:
            logging.exception("Error al actualizar información de la ruta:")
            return False
