# 🎫 Ticket Payment API - FastAPI

API moderna para sistema de pagos con tarjeta sin contacto mediante códigos QR, desarrollada con **FastAPI** y arquitectura de controladores modular.

## ✨ Características

- 🔐 **Autenticación JWT** con FastAPI Security
- 👤 **Registro y gestión de usuarios**
- 💳 **Gestión de métodos de pago**
- 📱 **Generación de códigos QR** para pagos
- 🔍 **Escaneo de códigos QR** para procesar pagos
- 💰 **Sistema de wallet** con recarga de saldo
- 📊 **Historial de transacciones** con estados detallados
- 🏗️ **Arquitectura modular** con controladores FastAPI
- 📚 **Documentación automática** con Swagger UI

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **MongoDB** - Base de datos NoSQL
- **JWT** - Autenticación con tokens
- **Pydantic** - Validación de datos
- **Uvicorn** - Servidor ASGI
- **Python 3.10+**

## 📋 Requisitos

- Python 3.10+ (probado con Python 3.13.5)
- MongoDB 5.0+
- pip (gestor de paquetes de Python)
- Docker y Docker Compose (opcional)

## 🚀 Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/ticket-payment-api.git
cd ticket-payment-api
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Crear archivo .env
SECRET_KEY=tu-clave-secreta-aqui
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=ticket_payment_db
ALGORITHM=HS256
```

### 5. Ejecutar el servidor
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Acceder a la documentación
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📡 API Endpoints

### 🔐 Autenticación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `POST` | `/api/register` | Registrar nuevo usuario | ✅ |
| `POST` | `/api/login` | Iniciar sesión | ✅ |
| `POST` | `/token` | OAuth2 token (compatibilidad) | ✅ |

### 👤 Usuario

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/user/profile` | Obtener perfil del usuario | ✅ |
| `GET` | `/api/user/qr` | Generar código QR personal | ✅ |

### 💳 Métodos de Pago

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/payment-methods` | Listar métodos de pago | ✅ |
| `POST` | `/api/payment-methods` | Agregar método de pago | ✅ |
| `DELETE` | `/api/payment-methods/{id}` | Eliminar método de pago | ✅ |

### 💰 Wallet

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/api/wallet/balance` | Obtener balance actual | ✅ |
| `POST` | `/api/wallet/topup` | Recargar saldo | ✅ |
| `GET` | `/api/wallet/transactions` | Historial de transacciones | ✅ |

### 💸 Pagos

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `POST` | `/api/payment/scan` | Procesar pago por QR | ✅ |

## 📝 Ejemplos de JSON

### Registro de Usuario
```json
POST /api/register
{
  "name": "example",
  "email": "example@example.com",
  "password": "MiClaveSegura123",
  "payment_method": {
    "card_holder": "example",
    "card_number": "4111111111111111",
    "expiry": "12/25",
    "cvv": "123"
  }
}
```

**Respuesta:**
```json
{
  "message": "Usuario registrado exitosamente",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "name": "example",
    "email": "example@example.com",
    "balance": 0.0
  }
}
```

### Login de Usuario
```json
POST /api/login
{
  "email": "example@example.com",
  "password": "MiClaveSegura123"
}
```

### Agregar Método de Pago
```json
POST /api/payment-methods
Authorization: Bearer <token>
{
  "card_holder": "example",
  "card_number": "5555555555554444",
  "expiry": "06/26",
  "cvv": "456"
}
```

### Recargar Wallet
```json
POST /api/wallet/topup
Authorization: Bearer <token>
{
  "amount": 100.0,
  "payment_method_id": "pm_123456789"
}
```

### Procesar Pago
```json
POST /api/payment/scan
Authorization: Bearer <token>
{
  "qr_data": "user_id:64f1a2b3c4d5e6f7g8h9i0j1",
  "amount": 25.50
}
```

## 🔒 Autenticación

La API utiliza **JWT (JSON Web Tokens)** para la autenticación. Después del login o registro, incluye el token en el header:

## 🧪 Pruebas

### Ejecutar suite de pruebas completa:
```bash
python pruebas/test_api.py
```

## 🏗️ Arquitectura

### Estructura del Proyecto
```
ticket-payment-api/
├── controllers/                    # 🎮 Controladores FastAPI
│   ├── auth/
│   │   └── controller.py          # Registro, login y OAuth2
│   ├── user/
│   │   └── controller.py          # Perfil, QR, cambio de contraseña
│   ├── payment/
│   │   └── controller.py          # Pagos QR y métodos de pago
│   └── wallet/
│       └── controller.py          # Balance, recarga y transacciones
├── models/                         # 📊 Modelos de datos y esquemas
│   ├── auth/
│   │   └── schemas.py             # Pydantic schemas (Login, Register, Token, etc.)
│   ├── user/
│   │   └── model.py               # Modelo de usuario (MongoDB)
│   └── transaction/
│       └── model.py               # Modelo de transacciones (MongoDB)
├── services/                       # 🔧 Lógica de negocio
│   └── auth_service.py            # Autenticación JWT, hash passwords
├── middleware/                     # 🛡️ Middleware de autenticación
│   └── auth.py                    # Validación de tokens JWT
├── utils/                          # 🛠️ Utilidades del sistema
│   ├── message_codes.py           # Códigos de mensaje estandarizados
│   └── server_response.py         # Respuestas HTTP estandarizadas
├── db/                            # 🗄️ Configuración de base de datos
│   └── mongodb.py                 # Conexión y configuración MongoDB
├── pruebas/                       # 🧪 Scripts de prueba
│   └── test_api.py                # Suite completa de tests de API
├── main.py                        # 🚀 Punto de entrada FastAPI
├── service_routes.py              # 📋 Definición de rutas (legacy)
├── requirements.txt               # 📦 Dependencias Python
├── Dockerfile                     # 🐳 Configuración Docker
└── docker-compose.yml             # 🐳 Orquestación de servicios
```

### Controladores Modulares
- **AuthController**: Registro, login, OAuth2
- **UserController**: Perfil, generación QR
- **PaymentController**: Procesamiento de pagos
- **PaymentMethodController**: Gestión de métodos de pago
- **WalletController**: Balance, recarga, historial

## 📊 Estados de Transacciones

| Estado | Descripción |
|--------|-------------|
| `pending` | Transacción iniciada, pendiente de procesamiento |
| `completed` | Transacción completada exitosamente |
| `failed` | Transacción falló (ej: saldo insuficiente) |
| `refunded` | Transacción reembolsada |

## 🔧 Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta para JWT | `dev-secret-key` |
| `MONGO_URI` | URI de conexión a MongoDB | `mongodb://localhost:27017/` |
| `MONGO_DB_NAME` | Nombre de la base de datos | `ticket_payment_db` |
| `ALGORITHM` | Algoritmo para JWT | `HS256` |

### MongoDB no conecta
```bash
# Verificar que MongoDB esté ejecutándose
mongosh
# o
mongo
```

### Puerto 8000 ocupado
```bash
# Usar otro puerto
uvicorn main:app --reload --port 8001
```

## 📚 Documentación Adicional

- **Swagger UI**: http://localhost:8000/docs - Interfaz interactiva
- **ReDoc**: http://localhost:8000/redoc - Documentación alternativa
- **OpenAPI Schema**: http://localhost:8000/openapi.json - Esquema JSON

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

