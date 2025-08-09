@echo off
echo ========================================
echo    PRUEBAS API - TICKET PAYMENT SYSTEM
echo ========================================
echo.

set BASE_URL=http://localhost:8000

echo [1/13] Verificando servidor...
curl -s -w "Status: %%{http_code}\n" %BASE_URL%/
echo.

echo [2/13] Registrando usuario...
curl -s -X POST %BASE_URL%/api/register ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"password\":\"password123\",\"payment_method\":{\"card_number\":\"1234567890123456\",\"expiry\":\"12/25\",\"cvv\":\"123\"}}" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [3/13] Login de usuario...
for /f "tokens=*" %%i in ('curl -s -X POST %BASE_URL%/api/login -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}" ^| jq -r .access_token') do set TOKEN=%%i
echo Token obtenido: %TOKEN:~0,20%...
echo.

echo [4/13] Obteniendo perfil...
curl -s -X GET %BASE_URL%/api/user/profile ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [5/13] Generando QR...
curl -s -X GET %BASE_URL%/api/user/qr ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [6/13] Listando métodos de pago...
curl -s -X GET %BASE_URL%/api/payment/methods ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [7/13] Agregando método de pago...
curl -s -X POST %BASE_URL%/api/payment/methods ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -d "{\"card_number\":\"9876543210987654\",\"expiry\":\"06/26\",\"cvv\":\"456\"}" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [8/13] Consultando balance...
curl -s -X GET %BASE_URL%/api/wallet ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [9/13] Recargando billetera...
curl -s -X POST %BASE_URL%/api/wallet/topup ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -d "{\"amount\":100.0,\"payment_method_id\":\"test-method\"}" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [10/13] Realizando pago por QR...
curl -s -X POST %BASE_URL%/api/payment/scan ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -d "{\"qr_data\":\"test-qr\",\"amount\":25.0}" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [11/13] Balance después del pago...
curl -s -X GET %BASE_URL%/api/wallet ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [12/13] Login OAuth2...
curl -s -X POST %BASE_URL%/token ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=test@example.com&password=password123" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo [13/13] Eliminando método de pago (debería fallar)...
curl -s -X DELETE %BASE_URL%/api/payment/methods/test-method-id ^
  -H "Authorization: Bearer %TOKEN%" ^
  -w "\nStatus: %%{http_code}\n"
echo.

echo ========================================
echo       PRUEBAS COMPLETADAS
echo ========================================
