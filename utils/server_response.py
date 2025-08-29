from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

class ServerResponse:
    @staticmethod
    def create_response(data: Any = None, message: Optional[str] = None, status: int = 200, message_code: Optional[str] = None, **kwargs) -> JSONResponse:
        """
        Crea una respuesta estandarizada para la API FastAPI
        """
        response = {
            'success': 200 <= status < 300,
            'status': status,
        }
        
        if message:
            response['message'] = message
            
        if message_code:
            response['message_code'] = message_code
            
        if data is not None:
            response['data'] = data
            
        # Agregar campos adicionales si se proporcionan
        response.update(kwargs)
        
        return JSONResponse(content=response, status_code=status)
    
    @classmethod
    def success(cls, data: Any = None, message: str = "Operación exitosa", status: int = 200, **kwargs) -> JSONResponse:
        return cls.create_response(data=data, message=message, status=status, **kwargs)
    
    @classmethod
    def error(cls, message: str = "Error en la operación", status: int = 400, message_code: Optional[str] = None, **kwargs) -> JSONResponse:
        return cls.create_response(
            data=None, 
            message=message, 
            status=status, 
            message_code=message_code,
            **kwargs
        )
    
    @classmethod
    def not_found(cls, message: str = "Recurso no encontrado", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=404, **kwargs)
    
    @classmethod
    def unauthorized(cls, message: str = "No autorizado", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=401, **kwargs)
    
    @classmethod
    def forbidden(cls, message: str = "Acceso denegado", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=403, **kwargs)
    
    @classmethod
    def bad_request(cls, message: str = "Solicitud incorrecta", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=400, **kwargs)
    
    @classmethod
    def server_error(cls, message: str = "Error interno del servidor", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=500, **kwargs)

    @classmethod
    def user_not_found(cls, **kwargs) -> JSONResponse:
        return cls.error(message="Usuario no encontrado", status=404, message_code="USER_NOT_FOUND", **kwargs)

    @classmethod
    def payment_method_not_found(cls, **kwargs) -> JSONResponse:
        return cls.error(message="Método de pago no encontrado", status=404, message_code="PAYMENT_METHOD_NOT_FOUND", **kwargs)

    @classmethod
    def insufficient_balance(cls, required_amount: Optional[float] = None, current_balance: Optional[float] = None, **kwargs) -> JSONResponse:
        data = {}
        if required_amount is not None:
            data['required_amount'] = required_amount
        if current_balance is not None:
            data['current_balance'] = current_balance
        return cls.error(
            message="Saldo insuficiente",
            status=402,
            message_code="INSUFFICIENT_BALANCE",
            data=data if data else None,
            **kwargs
        )

    @classmethod
    def validation_error(cls, message: str = "Datos de entrada inválidos", **kwargs) -> JSONResponse:
        return cls.error(message=message, status=400, message_code="VALIDATION_ERROR", **kwargs)

    @classmethod
    def user_already_exists(cls, **kwargs) -> JSONResponse:
        return cls.error(message="El correo electrónico ya está registrado", status=400, message_code="USER_ALREADY_EXISTS", **kwargs)

    @classmethod
    def weak_password(cls, **kwargs) -> JSONResponse:
        return cls.error(message="La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas y números", status=400, message_code="WEAK_PASSWORD", **kwargs)

    @classmethod
    def invalid_email(cls, **kwargs) -> JSONResponse:
        return cls.error(message="Formato de correo electrónico inválido", status=400, message_code="INVALID_EMAIL", **kwargs)

