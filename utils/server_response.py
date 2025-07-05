from flask import jsonify

class ServerResponse:
    @staticmethod
    def create_response(data=None, message=None, status=200, message_code=None, **kwargs):
        """
        Crea una respuesta estandarizada para la API
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
        
        return jsonify(response), status
    
    @classmethod
    def success(cls, data=None, message="Operación exitosa", status=200, **kwargs):
        return cls.create_response(data=data, message=message, status=status, **kwargs)
    
    @classmethod
    def error(cls, message="Error en la operación", status=400, message_code=None, **kwargs):
        return cls.create_response(
            data=None, 
            message=message, 
            status=status, 
            message_code=message_code,
            **kwargs
        )
    
    @classmethod
    def not_found(cls, message="Recurso no encontrado", **kwargs):
        return cls.error(message=message, status=404, **kwargs)
    
    @classmethod
    def unauthorized(cls, message="No autorizado", **kwargs):
        return cls.error(message=message, status=401, **kwargs)
    
    @classmethod
    def forbidden(cls, message="Acceso denegado", **kwargs):
        return cls.error(message=message, status=403, **kwargs)
    
    @classmethod
    def bad_request(cls, message="Solicitud incorrecta", **kwargs):
        return cls.error(message=message, status=400, **kwargs)
    
    @classmethod
    def server_error(cls, message="Error interno del servidor", **kwargs):
        return cls.error(message=message, status=500, **kwargs)

    @classmethod
    def user_not_found(cls, **kwargs):
        return cls.error(message="Usuario no encontrado", status=404, message_code="USER_NOT_FOUND", **kwargs)

    @classmethod
    def payment_method_not_found(cls, **kwargs):
        return cls.error(message="Método de pago no encontrado", status=404, message_code="PAYMENT_METHOD_NOT_FOUND", **kwargs)

    @classmethod
    def insufficient_balance(cls, required_amount=None, current_balance=None, **kwargs):
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
    def validation_error(cls, message="Datos de entrada inválidos", **kwargs):
        return cls.error(message=message, status=400, message_code="VALIDATION_ERROR", **kwargs)

    @classmethod
    def user_already_exists(cls, **kwargs):
        return cls.error(message="El correo electrónico ya está registrado", status=400, message_code="USER_ALREADY_EXISTS", **kwargs)

    @classmethod
    def weak_password(cls, **kwargs):
        return cls.error(message="La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas y números", status=400, message_code="WEAK_PASSWORD", **kwargs)

    @classmethod
    def invalid_email(cls, **kwargs):
        return cls.error(message="Formato de correo electrónico inválido", status=400, message_code="INVALID_EMAIL", **kwargs)

