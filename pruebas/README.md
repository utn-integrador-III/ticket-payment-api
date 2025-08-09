# 🧪 Pruebas de API - Ticket Payment System

Esta carpeta contiene scripts para probar todas las rutas de la API del sistema de pagos con QR.

## 📁 Archivos Incluidos

- **`test_api.py`** - Script principal de pruebas en Python con salida colorida
- **`test_curl.bat`** - Script de pruebas usando curl para Windows
- **`requirements.txt`** - Dependencias necesarias para el script Python
- **`README.md`** - Este archivo de documentación

## 🚀 Cómo Ejecutar las Pruebas

### Opción 1: Script Python (Recomendado)

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Asegúrate de que la API esté ejecutándose:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Ejecutar las pruebas:**
   ```bash
   python pruebas/test_api.py
   ```

### Opción 2: Script Curl (Windows)

1. **Asegúrate de que curl esté instalado** (viene por defecto en Windows 10+)

2. **Ejecutar el script:**
   ```cmd
   test_curl.bat
   ```

## 🔍 Rutas Probadas

El script prueba todas las siguientes rutas de la API:

### 🏠 Rutas Básicas
- `GET /` - Verificar que el servidor esté funcionando

### 👤 Autenticación
- `POST /api/register` - Registrar nuevo usuario
- `POST /api/login` - Login con credenciales JSON
- `POST /token` - Login OAuth2 con form data

### 👥 Usuario
- `GET /api/user/profile` - Obtener perfil del usuario
- `GET /api/user/qr` - Generar código QR del usuario

### 💳 Métodos de Pago
- `GET /api/payment/methods` - Listar métodos de pago
- `POST /api/payment/methods` - Agregar método de pago
- `DELETE /api/payment/methods/{id}` - Eliminar método de pago

### 💰 Billetera
- `GET /api/wallet` - Consultar balance
- `POST /api/wallet/topup` - Recargar saldo

### 🔄 Pagos
- `POST /api/payment/scan` - Realizar pago por QR

## 📊 Interpretación de Resultados

### ✅ Códigos de Estado Exitosos
- **200** - Operación exitosa
- **201** - Recurso creado exitosamente

### ❌ Códigos de Estado de Error
- **400** - Error en los datos enviados
- **401** - No autorizado (token inválido/faltante)
- **404** - Recurso no encontrado
- **500** - Error interno del servidor

## 🎨 Características del Script Python

- **Salida colorida** para fácil lectura
- **Manejo de errores** robusto
- **Información detallada** de cada request/response
- **Pruebas secuenciales** que usan datos de pruebas anteriores
- **Verificación automática** de códigos de estado

## 📝 Datos de Prueba

El script utiliza los siguientes datos de prueba:

```json
{
  "name": "Usuario Test",
  "email": "test@example.com",
  "password": "password123",
  "payment_method": {
    "card_number": "1234567890123456",
    "expiry": "12/25",
    "cvv": "123"
  }
}
```

## ⚠️ Notas Importantes

1. **Servidor Local**: Las pruebas asumen que la API está ejecutándose en `http://localhost:8000`
2. **Base de Datos**: Cada ejecución puede crear nuevos usuarios de prueba
3. **Tokens**: Los tokens JWT se obtienen automáticamente durante las pruebas
4. **Limpieza**: Considera limpiar datos de prueba de la base de datos periódicamente

## 🔧 Personalización

Para modificar las pruebas:

1. **Cambiar URL base**: Modifica `BASE_URL` en `test_api.py`
2. **Datos de prueba**: Modifica `TEST_USER` en `test_api.py`
3. **Agregar nuevas pruebas**: Añade llamadas a `test_endpoint()` en la función `main()`

## 🐛 Solución de Problemas

### Error de Conexión
```
❌ No se pudo conectar al servidor. ¿Está ejecutándose la API?
```
**Solución**: Verifica que la API esté ejecutándose en el puerto 8000

### Error de Token
```
❌ Test falló - Esperado: 200, Obtenido: 401
```
**Solución**: Problema con autenticación, verifica que el registro/login funcione correctamente

### Error de Dependencias
```
ModuleNotFoundError: No module named 'requests'
```
**Solución**: Ejecuta `pip install -r requirements.txt`
