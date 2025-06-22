from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from decouple import config
from service import add_service_layer
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config('SECRET_KEY', default='dev-secret-key')

# Configuración de CORS
if config('ENVIRONMENT', 'development') == 'development':
    CORS(app, resources={
        r"/api/*": {"origins": "*"}
    })

api = Api(app, prefix='/api')

# Agregar capa de servicios
add_service_layer(api)

if __name__ == "__main__":
    host = config('HOST', '0.0.0.0')
    port = config('PORT', 5000)
    debug = config('DEBUG', 'True').lower() in ('true', '1', 't')
    
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
