from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from decouple import config
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    _client = None
    db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa la conexión a MongoDB"""
        try:
            # Obtener configuración de variables de entorno
            mongo_uri = config('MONGO_URI', default='mongodb://localhost:27017/') # mongodb+srv://utnuser:utnus3r24@cluster0.d9lhmxd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
            db_name = config('MONGO_DB_NAME', default='ticket_payment_db')
            
            # Conectar a MongoDB
            self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Verificar la conexión
            self._client.admin.command('ping')
            
            # Seleccionar la base de datos
            self.db = self._client[db_name]
            
            logger.info("Conexión exitosa a MongoDB")
            
            # Crear índices
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Crea índices para optimizar consultas frecuentes"""
        try:
            # Índice para búsqueda por email (único)
            self.db.users.create_index([("email", 1)], unique=True)
            
            # Índice para búsqueda de métodos de pago
            self.db.users.create_index([("payment_methods.id", 1)])
            
            # Índice para transacciones
            self.db.transactions.create_index([("user_id", 1)])
            self.db.transactions.create_index([("created_at", -1)])
            
            logger.info("Índices creados exitosamente")
            
        except Exception as e:
            logger.error(f"Error al crear índices: {e}")
            raise
    
    def close_connection(self):
        """Cierra la conexión a MongoDB"""
        if self._client:
            self._client.close()
            logger.info("Conexión a MongoDB cerrada")

# Instancia global de la base de datos
db = MongoDB().db
