from fastapi import Depends, HTTPException
from utils.server_response import ServerResponse
from utils.message_codes import (
    INSUFFICIENT_BALANCE, PAYMENT_PROCESSED_BY_DRIVER, ROUTE_NOT_FOUND, 
    DRIVER_NOT_ASSIGNED_TO_ROUTE, INVALID_QR_CODE
)
from models.user.model import UserModel
from models.driver.model import DriverModel
from models.route.model import RouteModel
from models.transaction.model import TransactionModel, TransactionType, TransactionStatus
from models.auth.schemas import DriverScanRequest
from middleware.auth import get_current_driver
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DriverPaymentController:
    @staticmethod
    def scan_payment_by_driver(scan_data: DriverScanRequest, current_driver: DriverModel = Depends(get_current_driver)):
        """
        Procesar pago por escaneo de QR realizado por un chofer
        El monto se obtiene de la ruta especificada
        """
        try:
            # 1. Verificar que la ruta existe y está activa
            route = RouteModel.find_by_code(scan_data.route_code)
            if not route:
                return ServerResponse.error(
                    message="Ruta no encontrada",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=404
                )
            
            if not route.is_active:
                return ServerResponse.error(
                    message="La ruta no está activa",
                    message_code=ROUTE_NOT_FOUND,
                    status_code=400
                )
            
            # 2. Verificar que el chofer está asignado a esta ruta
            if str(current_driver._id) not in route.assigned_drivers:
                return ServerResponse.error(
                    message="No tienes permisos para cobrar en esta ruta",
                    message_code=DRIVER_NOT_ASSIGNED_TO_ROUTE,
                    status_code=403
                )
            
            # 3. Obtener el monto de la ruta
            fare_amount = route.fare_amount
            if fare_amount <= 0:
                return ServerResponse.error(
                    message="La ruta no tiene una tarifa válida configurada",
                    status_code=400
                )
            
            # 4. Extraer información del usuario del QR code
            # Asumiendo que el QR contiene el ID del usuario
            try:
                # El QR debería contener información del usuario
                # Por simplicidad, asumimos que contiene el user_id
                user_id = scan_data.qr_data.strip()
                user = UserModel.find_by_id(user_id)
                
                if not user:
                    return ServerResponse.error(
                        message="Usuario no válido en el código QR",
                        message_code=INVALID_QR_CODE,
                        status_code=400
                    )
            except Exception as e:
                logger.error(f"Error al procesar QR code: {str(e)}")
                return ServerResponse.error(
                    message="Código QR inválido",
                    message_code=INVALID_QR_CODE,
                    status_code=400
                )
            
            # 5. Verificar saldo suficiente ANTES de crear la transacción
            if user.balance < fare_amount:
                # Crear transacción rechazada por saldo insuficiente
                try:
                    transaction = TransactionModel.create(
                        user_id=str(user._id),
                        amount=-fare_amount,
                        transaction_type=TransactionType.PAYMENT,
                        description=f"Pago de pasaje rechazado - Saldo insuficiente - Ruta: {route.name} ({route.code})",
                        metadata={
                            "route_code": route.code,
                            "route_name": route.name,
                            "driver_id": str(current_driver._id),
                            "driver_name": current_driver.name,
                            "rejection_reason": "insufficient_balance"
                        }
                    )
                    transaction.update_status(TransactionStatus.FAILED)
                except Exception as e:
                    logger.warning(f"Error al registrar transacción rechazada: {str(e)}")
                
                return ServerResponse.insufficient_balance(
                    required_amount=fare_amount, 
                    current_balance=user.balance
                )
            
            # 6. Crear transacción y procesar pago
            transaction = None
            try:
                # Crear transacción
                transaction = TransactionModel.create(
                    user_id=str(user._id),
                    amount=-fare_amount,  # Negativo porque es un pago
                    transaction_type=TransactionType.PAYMENT,
                    description=f"Pago de pasaje - Ruta: {route.name} ({route.code})",
                    metadata={
                        "route_code": route.code,
                        "route_name": route.name,
                        "route_id": str(route._id),
                        "driver_id": str(current_driver._id),
                        "driver_name": current_driver.name,
                        "driver_license": current_driver.license_number,
                        "fare_amount": fare_amount,
                        "payment_method": "qr_scan_by_driver"
                    }
                )
                
                # Procesar el pago (actualizar balance del usuario)
                new_balance = user.balance - fare_amount
                if user.update_balance(new_balance):
                    # Marcar transacción como completada
                    transaction.update_status(TransactionStatus.COMPLETED)
                    
                    return ServerResponse.success(
                        data={
                            "transaction_id": str(transaction._id),
                            "user": {
                                "id": str(user._id),
                                "name": user.name,
                                "new_balance": user.balance
                            },
                            "route": {
                                "code": route.code,
                                "name": route.name,
                                "fare_amount": fare_amount
                            },
                            "driver": {
                                "id": str(current_driver._id),
                                "name": current_driver.name,
                                "license": current_driver.license_number
                            },
                            "payment_details": {
                                "amount_charged": fare_amount,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        },
                        message=f"Pago procesado exitosamente - ${fare_amount}",
                        message_code=PAYMENT_PROCESSED_BY_DRIVER
                    )
                else:
                    # Error al actualizar balance - marcar como fallida
                    transaction.update_status(TransactionStatus.FAILED)
                    return ServerResponse.server_error(message="Error al procesar el pago")
                    
            except HTTPException:
                # Re-lanzar HTTPException
                raise
            except Exception as e:
                # Error inesperado - marcar transacción como fallida si existe
                if transaction:
                    transaction.update_status(TransactionStatus.FAILED)
                logger.error(f"Error inesperado en pago por chofer: {str(e)}")
                raise HTTPException(status_code=500, detail="Error interno del servidor")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error general en scan_payment_by_driver: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_payment_history(current_driver: DriverModel = Depends(get_current_driver)):
        """
        Obtener historial de pagos procesados por el chofer
        """
        try:
            # Buscar transacciones donde el chofer fue quien procesó el pago
            from db.mongodb import db
            
            transactions_data = db.transactions.find({
                "metadata.driver_id": str(current_driver._id),
                "transaction_type": TransactionType.PAYMENT.value
            }).sort("created_at", -1).limit(50)
            
            transactions = []
            for trans_data in transactions_data:
                transactions.append({
                    "id": str(trans_data["_id"]),
                    "amount": abs(trans_data["amount"]),  # Mostrar como positivo
                    "status": trans_data["status"],
                    "description": trans_data["description"],
                    "route_info": {
                        "code": trans_data["metadata"].get("route_code", ""),
                        "name": trans_data["metadata"].get("route_name", "")
                    },
                    "created_at": trans_data["created_at"].isoformat() if hasattr(trans_data["created_at"], 'isoformat') else trans_data["created_at"]
                })
            
            return ServerResponse.success(
                data={
                    "transactions": transactions,
                    "count": len(transactions),
                    "driver": {
                        "id": str(current_driver._id),
                        "name": current_driver.name,
                        "license": current_driver.license_number
                    }
                },
                message="Historial de pagos obtenido exitosamente"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener historial de pagos del chofer: {str(e)}")
            return ServerResponse.server_error()

    @staticmethod
    def get_daily_summary(current_driver: DriverModel = Depends(get_current_driver)):
        """
        Obtener resumen diario de pagos procesados por el chofer
        """
        try:
            from db.mongodb import db
            from datetime import datetime, timedelta
            
            # Obtener transacciones del día actual
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            pipeline = [
                {
                    "$match": {
                        "metadata.driver_id": str(current_driver._id),
                        "transaction_type": TransactionType.PAYMENT.value,
                        "status": TransactionStatus.COMPLETED.value,
                        "created_at": {
                            "$gte": today_start,
                            "$lt": today_end
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_amount": {"$sum": {"$abs": "$amount"}},
                        "total_transactions": {"$sum": 1},
                        "routes": {"$addToSet": "$metadata.route_code"}
                    }
                }
            ]
            
            result = list(db.transactions.aggregate(pipeline))
            
            if result:
                summary = result[0]
                return ServerResponse.success(
                    data={
                        "daily_summary": {
                            "date": today_start.strftime("%Y-%m-%d"),
                            "total_amount_collected": summary["total_amount"],
                            "total_transactions": summary["total_transactions"],
                            "routes_served": len(summary["routes"]),
                            "route_codes": summary["routes"]
                        },
                        "driver": {
                            "id": str(current_driver._id),
                            "name": current_driver.name,
                            "license": current_driver.license_number
                        }
                    },
                    message="Resumen diario obtenido exitosamente"
                )
            else:
                return ServerResponse.success(
                    data={
                        "daily_summary": {
                            "date": today_start.strftime("%Y-%m-%d"),
                            "total_amount_collected": 0,
                            "total_transactions": 0,
                            "routes_served": 0,
                            "route_codes": []
                        },
                        "driver": {
                            "id": str(current_driver._id),
                            "name": current_driver.name,
                            "license": current_driver.license_number
                        }
                    },
                    message="No hay transacciones para hoy"
                )
            
        except Exception as e:
            logger.error(f"Error al obtener resumen diario del chofer: {str(e)}")
            return ServerResponse.server_error()
