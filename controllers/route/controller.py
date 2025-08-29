from fastapi import Depends
from utils.server_response import ServerResponse
from utils.message_codes import (
    ROUTE_CREATED, ROUTE_UPDATED, ROUTE_DELETED, ROUTE_NOT_FOUND, 
    ROUTE_ALREADY_EXISTS, DRIVER_ROUTE_ASSIGNED, DRIVER_NOT_FOUND,
    DRIVER_NOT_ASSIGNED_TO_ROUTE, INVALID_ROUTE_DATA
)
from models.route.model import RouteModel
from models.driver.model import DriverModel
from models.auth.schemas import RouteCreateRequest, RouteUpdateRequest, RouteAssignmentRequest
from middleware.auth import get_current_driver
import logging

logger = logging.getLogger(__name__)

class RouteController:
    @staticmethod
    def create_route(route_data: RouteCreateRequest):
        """
        Crear nueva ruta
        """
        try:
            # Verificar si ya existe una ruta con el mismo código
            if RouteModel.find_by_code(route_data.code):
                return ServerResponse.error(
                    message="Ya existe una ruta con este código",
                    message_code=ROUTE_ALREADY_EXISTS,
                    status_code=409
                )
            
            # Crear datos de la ruta
            route_dict = {
                "name": route_data.name,
                "code": route_data.code,
                "description": route_data.description or "",
                "origin": route_data.origin,
                "destination": route_data.destination,
                "stops": route_data.stops or [],
                "fare_amount": route_data.fare_amount,
                "distance_km": route_data.distance_km or 0.0,
                "estimated_duration": route_data.estimated_duration or 0,
                "assigned_drivers": [],
                "is_active": True,
                "schedule": route_data.schedule or {}
            }
            
            # Crear ruta
            route = RouteModel.create(route_dict)
            if not route:
                return ServerResponse.server_error(message="Error al crear ruta")
            
            return ServerResponse.success(
                data={"route": route.to_dict()},
                message="Ruta creada exitosamente",
                message_code=ROUTE_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error al crear ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_route(route_id: str):
        """
        Obtener ruta por ID
        """
        try:
            route = RouteModel.find_by_id(route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            return ServerResponse.success(
                data={"route": route.to_dict()},
                message="Ruta obtenida exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_route_by_code(route_code: str):
        """
        Obtener ruta por código
        """
        try:
            route = RouteModel.find_by_code(route_code)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            return ServerResponse.success(
                data={"route": route.to_dict()},
                message="Ruta obtenida exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener ruta por código: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_all_routes():
        """
        Obtener todas las rutas activas
        """
        try:
            routes = RouteModel.get_all_active()
            routes_data = [route.to_dict() for route in routes]
            
            return ServerResponse.success(
                data={
                    "routes": routes_data,
                    "count": len(routes_data)
                },
                message="Rutas obtenidas exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener rutas: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def update_route(route_id: str, route_data: RouteUpdateRequest):
        """
        Actualizar ruta
        """
        try:
            route = RouteModel.find_by_id(route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            # Preparar datos de actualización
            update_data = {}
            for field, value in route_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            if not update_data:
                return ServerResponse.error(
                    message="No hay datos para actualizar",
                    message_code=INVALID_ROUTE_DATA,
                    status_code=400
                )
            
            # Actualizar ruta
            if route.update_route_info(update_data):
                return ServerResponse.success(
                    data={"route": route.to_dict()},
                    message="Ruta actualizada exitosamente",
                    message_code=ROUTE_UPDATED
                )
            else:
                return ServerResponse.server_error(message="Error al actualizar ruta")
            
        except Exception as e:
            logger.error(f"Error al actualizar ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def delete_route(route_id: str):
        """
        Eliminar ruta (marcar como inactiva)
        """
        try:
            route = RouteModel.find_by_id(route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            if route.update_status(False):
                return ServerResponse.success(
                    message="Ruta eliminada exitosamente",
                    message_code=ROUTE_DELETED
                )
            else:
                return ServerResponse.server_error(message="Error al eliminar ruta")
            
        except Exception as e:
            logger.error(f"Error al eliminar ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def assign_driver_to_route(assignment_data: RouteAssignmentRequest):
        """
        Asignar chofer a ruta
        """
        try:
            # Verificar que la ruta existe
            route = RouteModel.find_by_id(assignment_data.route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            # Verificar que el chofer existe
            driver = DriverModel.find_by_id(assignment_data.driver_id)
            if not driver:
                return ServerResponse.error(
                    message="Chofer no encontrado",
                    message_code=DRIVER_NOT_FOUND,
                    status_code=404
                )
            
            # Asignar chofer a la ruta
            if route.assign_driver(assignment_data.driver_id):
                # También asignar la ruta al chofer
                driver.assign_route(assignment_data.route_id)
                
                return ServerResponse.success(
                    data={
                        "route": route.to_dict(),
                        "driver": driver.to_dict()
                    },
                    message="Chofer asignado a la ruta exitosamente",
                    message_code=DRIVER_ROUTE_ASSIGNED
                )
            else:
                return ServerResponse.server_error(message="Error al asignar chofer a la ruta")
            
        except Exception as e:
            logger.error(f"Error al asignar chofer a ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def remove_driver_from_route(assignment_data: RouteAssignmentRequest):
        """
        Remover chofer de ruta
        """
        try:
            # Verificar que la ruta existe
            route = RouteModel.find_by_id(assignment_data.route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            # Verificar que el chofer existe
            driver = DriverModel.find_by_id(assignment_data.driver_id)
            if not driver:
                return ServerResponse.error(
                    message="Chofer no encontrado",
                    message_code=DRIVER_NOT_FOUND,
                    status_code=404
                )
            
            # Verificar que el chofer está asignado a la ruta
            if assignment_data.driver_id not in route.assigned_drivers:
                return ServerResponse.error(
                    message="El chofer no está asignado a esta ruta",
                    message_code=DRIVER_NOT_ASSIGNED_TO_ROUTE,
                    status_code=400
                )
            
            # Remover chofer de la ruta
            if route.remove_driver(assignment_data.driver_id):
                # También remover la ruta del chofer
                driver.remove_route(assignment_data.route_id)
                
                return ServerResponse.success(
                    data={
                        "route": route.to_dict(),
                        "driver": driver.to_dict()
                    },
                    message="Chofer removido de la ruta exitosamente"
                )
            else:
                return ServerResponse.server_error(message="Error al remover chofer de la ruta")
            
        except Exception as e:
            logger.error(f"Error al remover chofer de ruta: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_driver_routes(current_driver: DriverModel = Depends(get_current_driver)):
        """
        Obtener rutas asignadas al chofer actual
        """
        try:
            routes = RouteModel.find_by_driver(str(current_driver._id))
            routes_data = [route.to_dict() for route in routes]
            
            return ServerResponse.success(
                data={
                    "routes": routes_data,
                    "count": len(routes_data)
                },
                message="Rutas del chofer obtenidas exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener rutas del chofer: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def update_route_fare(route_id: str, new_fare: float):
        """
        Actualizar tarifa de la ruta
        """
        try:
            route = RouteModel.find_by_id(route_id)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            if new_fare <= 0:
                return ServerResponse.error(
                    message="La tarifa debe ser mayor a 0",
                    message_code=INVALID_ROUTE_DATA,
                    status_code=400
                )
            
            if route.update_fare(new_fare):
                return ServerResponse.success(
                    data={"route": route.to_dict()},
                    message="Tarifa actualizada exitosamente",
                    message_code=ROUTE_UPDATED
                )
            else:
                return ServerResponse.server_error(message="Error al actualizar tarifa")
            
        except Exception as e:
            logger.error(f"Error al actualizar tarifa: {str(e)}")
            return ServerResponse.server_error()
