# Ticket Payment API

API para el sistema de pagos con tarjeta sin contacto mediante códigos QR.

## Características

- Registro de usuarios con métodos de pago
- Autenticación con JWT
- Generación de códigos QR para pagos
- Escaneo de códigos QR para procesar pagos
- Recarga de saldo
- Gestión de métodos de pago
- Historial de transacciones

## Requisitos

- Python 3.10+ (probado con Python 3.13.5)
- MongoDB 5.0+
- pip (gestor de paquetes de Python)
- Docker y Docker Compose (opcional)

## Instalación

1. Clonar el repositorio:
   git clone https://github.com/tu-usuario/ticket-payment-api.git
   cd ticket-payment-api

2. Crear un entorno virtual (recomendado):
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Configurar variables de entorno:
   cp .env.example .env
   Editar el archivo `.env` con tus configuraciones.

## Ejecución

### Ejecución local (sin Docker)
1. Crea un entorno virtual y actívalo (opcional):

   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   .\venv\Scripts\activate.bat
   .\venv\Scripts\activate.ps1

2. Instala las dependencias:

   pip install -r requirements.txt

3. Copia y ajusta las variables de entorno:

   cp .env.example .env

4. Inicia el servidor con recarga automática:

   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   La API quedará disponible en `http://localhost:8000` y la documentación en `http://localhost:8000/docs`.

## SI al momento de ejecutar el backend se presentan erorres usar la version de pythone 3.12
   py -3.12 -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt

Activate.ps1: Activa el entorno virtual de Python.
pip install -r requirements.txt: Instala las dependencias listadas en requirements.txt.
uvicorn main:app --reload --host 0.0.0.0 --port 8000: Inicia el servidor FastAPI en modo recarga.

### Ejecución con Docker (opcional)

1. Construye la imagen:
   docker build -t ticket-payment-api .
2. Ejecuta el contenedor:
   docker run -p 5000:5000 ticket-payment-api
   La API quedará disponible en `http://localhost:5000` y la documentación en `http://localhost:5000/docs`.

## Estructura del Proyecto

ticket-payment-api/
├── main.py                 # Punto de entrada de la aplicación FastAPI
├── service.py             # Configuración de rutas de la API
├── requirements.txt        # Dependencias de Python
├── .env.example           # Plantilla de variables de entorno
├── Dockerfile             # Configuración de Docker
├── docker-compose.yml     # Configuración de servicios con Docker
├── README.md             # Este archivo
│
├── controllers/          # Controladores de la API
│   ├── auth/             # Autenticación
│   ├── payment/          # Pagos y métodos de pago
│   ├── user/             # Perfil de usuario
│   └── wallet/           # Gestión de billetera
│
├── models/              # Modelos de datos
│   ├── user/             # Modelo de usuario
│   └── transaction/      # Modelo de transacciones
│
├── db/                  # Configuración de base de datos
│   └── mongodb.py        # Conexión a MongoDB
│
├── middleware/          # Middlewares
│   └── auth.py           # Autenticación JWT
│
└── utils/               # Utilidades
    ├── server_response.py # Respuestas estandarizadas
    └── message_codes.py  # Códigos de mensajes

## Documentación de la API

La documentación interactiva de la API está disponible en:
- Swagger UI (local): `http://localhost:8000/docs`
- Swagger UI (Docker): `http://localhost:5000/docs`
- Esquema OpenAPI: `http://localhost:8000/openapi.json`

### Endpoints Principales

#### Autenticación

- `POST /api/register` - Registrar nuevo usuario
- `POST /api/login` - Iniciar sesión
- `PUT /api/change-password` - Cambiar contraseña del usuario
- `POST /token` - Login OAuth2 (form data)
- `GET /` - Verificar estado del servidor

#### Usuario

- `GET /api/user/qr` - Generar código QR del usuario
- `GET /api/user/profile` - Obtener perfil del usuario

#### Pagos

- `POST /api/payment/scan` - Escanear código QR para pagar
- `GET /api/payment/methods` - Obtener métodos de pago
- `POST /api/payment/methods` - Agregar método de pago
- `DELETE /api/payment/methods/{id}` - Eliminar método de pago

#### Billetera

- `GET /api/wallet` - Obtener saldo
- `POST /api/wallet/topup` - Recargar saldo
- `GET /api/wallet/transactions` - Historial de transacciones

## Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `FASTAPI_APP` | Ruta ASGI de la aplicación | `main:app` |
| `ENVIRONMENT` | Entorno de ejecución | `development` |
| `SECRET_KEY` | Clave secreta para la aplicación | `dev-secret-key` |
| `MONGO_URI` | URI de conexión a MongoDB | `mongodb://localhost:27017/` |
| `MONGO_DB_NAME` | Nombre de la base de datos | `ticket_payment_db` |
| `JWT_SECRET_KEY` | Clave secreta para JWT | `jwt-secret-key` |
| `JWT_ACCESS_TOKEN_EXPIRES` | Tiempo de expiración del token de acceso (segundos) | `3600` (1 hora) |
| `JWT_REFRESH_TOKEN_EXPIRES` | Tiempo de expiración del token de actualización (segundos) | `2592000` (30 días) |

## Ejemplos de Uso

### Registrar un nuevo usuario

```http
POST /api/register
Content-Type: application/json

{
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "password": "MiClaveSegura123",
  "payment_method": {
    "card_holder": "Juan Pérez",
    "card_number": "4111111111111111",
    "expiry": "12/25",
    "cvv": "123"
  }
}
```

### Iniciar sesión (JSON)

```http
POST /api/login
Content-Type: application/json

{
  "email": "juan@example.com",
  "password": "MiClaveSegura123"
}
```

### Login OAuth2 (Form Data)

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=juan@example.com&password=MiClaveSegura123
```

### Agregar método de pago

```http
POST /api/payment/methods
Authorization: Bearer <token>
Content-Type: application/json

{
  "card_holder": "María García",
  "card_number": "5555555555554444",
  "expiry": "06/26",
  "cvv": "456"
}
```

### Recargar saldo

```http
POST /api/wallet/topup
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100.00,
  "payment_method_id": "pm_123456789"
}
```

### Realizar pago por QR

```http
POST /api/payment/scan
Authorization: Bearer <token>
Content-Type: application/json

{
  "qr_data": "user_id_or_merchant_code",
  "amount": 25.50
}
```

## Pruebas

Para ejecutar las pruebas:

python pruebas/test_api.py

## Despliegue

### Producción

1. Configurar un servidor web como Nginx o Apache como proxy inverso
2. Usar Gunicorn como servidor WSGI:
      gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
3. Configurar un servicio systemd para la aplicación
4. Configurar SSL con Let's Encrypt

### Variables de entorno en producción

Asegúrate de configurar las siguientes variables en producción:

FLASK_ENV=production
SECRET_KEY=una_clave_muy_larga_y_segura
JWT_SECRET_KEY=otra_clave_muy_larga_y_segura
MONGO_URI=mongodb://usuario:contraseña@servidor:27017/

## git-Command

1. Hacer fork del repositorio
2. Crear una rama para tu función (`git checkout -b feature/nueva-funcion`)
3. Preparar todos los archivos para commit (agrega todos los cambios nuevos y existentes) (`git add .`)
3. Hacer commit de tus cambios (`git commit -am 'Añadir nueva función'`)
4. Hacer push a la rama (`git push origin feature/nueva-funcion`)
5. Crear un Pull Request
