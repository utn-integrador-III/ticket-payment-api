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
