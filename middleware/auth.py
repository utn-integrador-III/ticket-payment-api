from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from utils.server_response import ServerResponse
from models.user.model import UserModel
import logging

def jwt_required_with_roles(roles=None):
    """
    Decorador personalizado que verifica el token JWT y los roles del usuario
    """
    if roles is None:
        roles = []
    
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                # Verificar que el token JWT sea válido
                verify_jwt_in_request()
                
                # Obtener la identidad del usuario desde el token
                user_id = get_jwt_identity()
                
                # Verificar que el usuario exista
                user = UserModel.find_by_id(user_id)
                if not user:
                    return ServerResponse.unauthorized("Usuario no encontrado")
                
                # Verificar roles si se especificaron
                if roles:
                    user_roles = get_jwt().get('roles', [])
                    if not any(role in user_roles for role in roles):
                        return ServerResponse.forbidden("Permisos insuficientes")
                
                # Pasar el usuario autenticado a la función
                kwargs['current_user'] = user
                return fn(*args, **kwargs)
                
            except Exception as e:
                logging.exception("Error en autenticación:")
                return ServerResponse.unauthorized("Token inválido o expirado")
        
        return decorator
    return wrapper

# Alias comúnmente usado
def auth_required(fn=None, roles=None):
    if fn:
        return jwt_required_with_roles(roles=roles)(fn)
    return jwt_required_with_roles(roles=roles)
