from flask_restful import Resource, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models.user.model import UserModel
from utils.server_response import ServerResponse
from utils.message_codes import *
import logging
import bcrypt
import re

class AuthController(Resource):
    def post(self):
        """
        Maneja tanto el registro como el inicio de sesión basado en el endpoint
        """
        endpoint = request.endpoint
        
        if endpoint == 'register':
            return self._register()
        elif endpoint == 'login':
            return self._login()
        
        return ServerResponse.error("Endpoint no válido", status=404)
    
    def _register(self):
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ['name', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return ServerResponse.validation_error(message=f"El campo {field} es requerido")
            
            # Validar formato de email
            if not self._is_valid_email(data['email']):
                return ServerResponse.invalid_email()
            
            # Validar fortaleza de la contraseña
            if not self._is_strong_password(data['password']):
                return ServerResponse.weak_password()
            
            # Verificar si el usuario ya existe
            if UserModel.find_by_email(data['email']):
                return ServerResponse.user_already_exists()
            
            # Crear hash de la contraseña
            hashed_password = self._hash_password(data['password'])
            
            # Crear objeto de usuario
            user_data = {
                'name': data['name'].strip(),
                'email': data['email'].lower().strip(),
                'password': hashed_password,
                'balance': 0.0,
                'payment_methods': []
            }
            
            # Agregar método de pago si se proporciona
            payment_method = data.get('payment_method')
            if payment_method:
                # Validar método de pago
                if not self._is_valid_card(payment_method):
                    return ServerResponse.error(
                        "Datos de tarjeta inválidos",
                        status=400,
                        message_code=INVALID_CARD
                    )
                
            # Guardar usuario en la base de datos
            user = UserModel.create(user_data)
            
            # Si hay un método de pago, guardarlo
            if payment_method:
                try:
                    user.add_payment_method(payment_method)
                except Exception as e:
                    logging.error(f"Error al guardar método de pago: {str(e)}")
                    # No fallamos el registro si hay error con el método de pago
            
            # Generar tokens de acceso
            access_token = create_access_token(identity=str(user._id))
            refresh_token = create_refresh_token(identity=str(user._id))
            
            return ServerResponse.success(
                data={
                    'message': 'Usuario registrado exitosamente',
                    'user_id': str(user._id),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                },
                status=201,
                message_code=USER_REGISTERED
            )
            
        except Exception as e:
            logging.exception("Error en el registro:")
            return ServerResponse.error(
                "Error al procesar el registro",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    def _login(self):
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            if not data.get('email') or not data.get('password'):
                return ServerResponse.error(
                    "Correo y contraseña son requeridos",
                    status=400,
                    message_code=VALIDATION_ERROR
                )
            
            # Buscar usuario
            user = UserModel.find_by_email(data['email'].lower().strip())
            
            # Verificar credenciales
            if not user or not self._check_password(data['password'], user.password):
                return ServerResponse.error(
                    "Credenciales inválidas",
                    status=401,
                    message_code=INVALID_CREDENTIALS
                )
            
            # Generar tokens
            access_token = create_access_token(identity=str(user._id))
            refresh_token = create_refresh_token(identity=str(user._id))
            
            return ServerResponse.success(
                data={
                    'message': 'Inicio de sesión exitoso',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user_id': str(user._id)
                },
                message_code=LOGIN_SUCCESSFUL
            )
            
        except Exception as e:
            logging.exception("Error en el inicio de sesión:")
            return ServerResponse.error(
                "Error al procesar el inicio de sesión",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _is_valid_email(email):
        """Valida el formato del correo electrónico"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def _is_strong_password(password):
        """
        Valida que la contraseña tenga al menos:
        - 8 caracteres
        - 1 mayúscula
        - 1 minúscula
        - 1 número
        """
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        return True
    
    @staticmethod
    def _hash_password(password):
        """Genera un hash seguro de la contraseña"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def _check_password(password, hashed_password):
        """Verifica si la contraseña coincide con el hash"""
        if not password or not hashed_password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def _is_valid_card(card_data):
        """Valida los datos básicos de una tarjeta"""
        try:
            # Validar número de tarjeta (solo verificar que sean dígitos y longitud)
            card_number = str(card_data.get('card_number', '')).replace(' ', '')
            if not (13 <= len(card_number) <= 19) or not card_number.isdigit():
                return False
                
            # Validar fecha de expiración (formato MM/YY)
            expiry = card_data.get('expiry', '')
            if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', expiry):
                return False
                
            # Validar CVV (3 o 4 dígitos)
            cvv = str(card_data.get('cvv', ''))
            if not (3 <= len(cvv) <= 4) or not cvv.isdigit():
                return False
                
            return True
            
        except Exception:
            return False

    def put(self):
        """
        Maneja la modificación de contraseña
        """
        endpoint = request.endpoint
        
        if endpoint == 'change_password':
            return self._change_password()
        
        return ServerResponse.error("Endpoint no válido", status=404)
    
    @jwt_required()
    def _change_password(self):
        """
        Cambia la contraseña del usuario autenticado
        """
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            if not data.get('current_password') or not data.get('new_password'):
                return ServerResponse.validation_error(
                    message="Contraseña actual y nueva contraseña son requeridas"
                )
            
            # Obtener ID del usuario del token JWT
            user_id = get_jwt_identity()
            
            # Buscar usuario
            user = UserModel.find_by_id(user_id)
            if not user:
                return ServerResponse.error(
                    "Usuario no encontrado",
                    status=404,
                    message_code=USER_NOT_FOUND
                )
            
            # Verificar contraseña actual
            if not self._check_password(data['current_password'], user.password):
                return ServerResponse.error(
                    "Contraseña actual incorrecta",
                    status=401,
                    message_code=INVALID_CREDENTIALS
                )
            
            # Validar fortaleza de la nueva contraseña
            if not self._is_strong_password(data['new_password']):
                return ServerResponse.weak_password()
            
            # Verificar que la nueva contraseña sea diferente a la actual
            if self._check_password(data['new_password'], user.password):
                return ServerResponse.error(
                    "La nueva contraseña debe ser diferente a la actual",
                    status=400,
                    message_code=VALIDATION_ERROR
                )
            
            # Generar hash de la nueva contraseña
            new_hashed_password = self._hash_password(data['new_password'])
            
            # Actualizar contraseña en la base de datos
            user.update_password(new_hashed_password)
            
            return ServerResponse.success(
                data={
                    'message': 'Contraseña actualizada exitosamente'
                },
                message_code=PASSWORD_UPDATED
            )
            
        except Exception as e:
            logging.exception("Error al cambiar contraseña:")
            return ServerResponse.error(
                "Error al procesar el cambio de contraseña",
                status=500,
                message_code=INTERNAL_SERVER_ERROR
            )
