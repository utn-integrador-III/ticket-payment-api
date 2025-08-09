#!/usr/bin/env python3
"""
Script de pruebas actualizado para la API de Ticket Payment (FastAPI)
Prueba todas las rutas disponibles y muestra los resultados en la terminal
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuración
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "name": "Usuario Test",
    "email": f"test_{int(time.time())}@example.com",  # Email único
    "password": "TestPassword123",
    "payment_method": {
        "card_holder": "Usuario Test",
        "card_number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123"
    }
}

class Colors:
    """Colores para la terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    """Imprime un encabezado colorido"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_test(test_name, method, endpoint):
    """Imprime información del test"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}🧪 Test: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}📡 {method} {endpoint}{Colors.END}")

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    """Imprime mensaje informativo"""
    print(f"{Colors.PURPLE}ℹ️  {message}{Colors.END}")

def print_response(response):
    """Imprime la respuesta de manera formateada"""
    try:
        data = response.json()
        print(f"{Colors.WHITE}📄 Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}{Colors.END}")
    except:
        print(f"{Colors.WHITE}📄 Respuesta: {response.text}{Colors.END}")

def test_endpoint(method, endpoint, data=None, headers=None, expected_status=200):
    """Función genérica para probar endpoints"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print_error(f"Método HTTP no soportado: {method}")
            return None
            
        print(f"{Colors.WHITE}🔄 Status: {response.status_code}{Colors.END}")
        
        if response.status_code == expected_status:
            print_success(f"Test exitoso - Status {response.status_code}")
            print_response(response)
            return response
        else:
            print_error(f"Test falló - Esperado: {expected_status}, Obtenido: {response.status_code}")
            print_response(response)
            return response
            
    except requests.exceptions.RequestException as e:
        print_error(f"Error de conexión: {e}")
        return None

def main():
    """Función principal que ejecuta todas las pruebas"""
    print_header("🚀 PRUEBAS DE API - TICKET PAYMENT SYSTEM")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Variables globales para almacenar datos de prueba
    access_token = None
    user_id = None
    payment_method_id = None
    
    # ==========================================
    # 1. PRUEBAS DE AUTENTICACIÓN
    # ==========================================
    print_header("🔐 PRUEBAS DE AUTENTICACIÓN")
    
    # Test 1: Registro de usuario
    print_test("Registro de Usuario", "POST", "/api/register")
    register_response = test_endpoint("POST", "/api/register", data=TEST_USER, expected_status=200)
    
    if register_response and register_response.status_code == 200:
        register_data = register_response.json()
        access_token = register_data.get("access_token")
        user_id = register_data.get("user", {}).get("id")
        print_success(f"Usuario registrado con ID: {user_id}")
        print_info(f"Token obtenido: {access_token[:20]}...")
    
    # Test 2: Login de usuario
    print_test("Login de Usuario", "POST", "/api/login")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    login_response = test_endpoint("POST", "/api/login", data=login_data, expected_status=200)
    
    # Test 3: OAuth2 Token (para compatibilidad)
    print_test("OAuth2 Token", "POST", "/token")
    oauth_data = {
        "username": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    # Usar form data para OAuth2
    try:
        oauth_response = requests.post(f"{BASE_URL}/token", data=oauth_data)
        print(f"{Colors.WHITE}🔄 Status: {oauth_response.status_code}{Colors.END}")
        if oauth_response.status_code == 200:
            print_success("OAuth2 Token obtenido exitosamente")
            print_response(oauth_response)
        else:
            print_error(f"Error en OAuth2 Token - Status: {oauth_response.status_code}")
            print_response(oauth_response)
    except Exception as e:
        print_error(f"Error en OAuth2: {e}")
    
    # Headers con autenticación
    auth_headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    
    # ==========================================
    # 2. PRUEBAS DE USUARIO
    # ==========================================
    print_header("👤 PRUEBAS DE USUARIO")
    
    # Test 4: Obtener perfil de usuario
    print_test("Obtener Perfil", "GET", "/api/user/profile")
    profile_response = test_endpoint("GET", "/api/user/profile", headers=auth_headers, expected_status=200)
    
    # Test 5: Generar código QR
    print_test("Generar Código QR", "GET", "/api/user/qr")
    qr_response = test_endpoint("GET", "/api/user/qr", headers=auth_headers, expected_status=200)
    
    # ==========================================
    # 3. PRUEBAS DE MÉTODOS DE PAGO
    # ==========================================
    print_header("💳 PRUEBAS DE MÉTODOS DE PAGO")
    
    # Test 6: Obtener métodos de pago
    print_test("Obtener Métodos de Pago", "GET", "/api/payment-methods")
    methods_response = test_endpoint("GET", "/api/payment-methods", headers=auth_headers, expected_status=200)
    
    if methods_response and methods_response.status_code == 200:
        methods_data = methods_response.json()
        if methods_data.get("payment_methods"):
            payment_method_id = methods_data["payment_methods"][0].get("id")
            print_info(f"Método de pago encontrado: {payment_method_id}")
    
    # Test 7: Agregar nuevo método de pago
    print_test("Agregar Método de Pago", "POST", "/api/payment-methods")
    new_payment_method = {
        "card_holder": "Nuevo Titular",
        "card_number": "5555555555554444",
        "expiry": "06/26",
        "cvv": "456"
    }
    add_method_response = test_endpoint("POST", "/api/payment-methods", data=new_payment_method, headers=auth_headers, expected_status=200)
    
    if add_method_response and add_method_response.status_code == 200:
        new_method_data = add_method_response.json()
        new_payment_method_id = new_method_data.get("payment_method", {}).get("id")
        if new_payment_method_id:
            print_info(f"Nuevo método agregado: {new_payment_method_id}")
            
            # Test 8: Eliminar método de pago
            print_test("Eliminar Método de Pago", "DELETE", f"/api/payment-methods/{new_payment_method_id}")
            delete_response = test_endpoint("DELETE", f"/api/payment-methods/{new_payment_method_id}", headers=auth_headers, expected_status=200)
    
    # ==========================================
    # 4. PRUEBAS DE WALLET
    # ==========================================
    print_header("💰 PRUEBAS DE WALLET")
    
    # Test 9: Obtener balance
    print_test("Obtener Balance", "GET", "/api/wallet/balance")
    balance_response = test_endpoint("GET", "/api/wallet/balance", headers=auth_headers, expected_status=200)
    
    # Test 10: Recargar wallet
    if payment_method_id:
        print_test("Recargar Wallet", "POST", "/api/wallet/topup")
        topup_data = {
            "amount": 100.0,
            "payment_method_id": payment_method_id
        }
        topup_response = test_endpoint("POST", "/api/wallet/topup", data=topup_data, headers=auth_headers, expected_status=200)
    else:
        print_info("⚠️  Saltando recarga de wallet - No hay método de pago disponible")
    
    # Test 11: Obtener historial de transacciones
    print_test("Historial de Transacciones", "GET", "/api/wallet/transactions")
    transactions_response = test_endpoint("GET", "/api/wallet/transactions", headers=auth_headers, expected_status=200)
    
    # Test 12: Historial paginado
    print_test("Historial Paginado", "GET", "/api/wallet/transactions?page=1&limit=5")
    paginated_response = test_endpoint("GET", "/api/wallet/transactions?page=1&limit=5", headers=auth_headers, expected_status=200)
    
    # ==========================================
    # 5. PRUEBAS DE PAGOS
    # ==========================================
    print_header("💸 PRUEBAS DE PAGOS")
    
    # Test 13: Escanear pago (simulación)
    print_test("Escanear Pago", "POST", "/api/payment/scan")
    
    # Primero necesitamos datos QR válidos del usuario
    if qr_response and qr_response.status_code == 200:
        qr_data = qr_response.json().get("qr_data", "")
        if qr_data:
            scan_data = {
                "qr_data": qr_data,
                "amount": 25.0
            }
            scan_response = test_endpoint("POST", "/api/payment/scan", data=scan_data, headers=auth_headers, expected_status=200)
        else:
            print_info("⚠️  No se pudo obtener datos QR válidos")
    else:
        print_info("⚠️  Saltando escaneo de pago - No hay datos QR disponibles")
    
    # ==========================================
    # 6. PRUEBAS DE DOCUMENTACIÓN
    # ==========================================
    print_header("📚 PRUEBAS DE DOCUMENTACIÓN")
    
    # Test 14: Documentación OpenAPI
    print_test("Documentación OpenAPI", "GET", "/openapi.json")
    openapi_response = test_endpoint("GET", "/openapi.json", expected_status=200)
    
    # Test 15: Documentación Swagger UI
    print_test("Swagger UI", "GET", "/docs")
    try:
        docs_response = requests.get(f"{BASE_URL}/docs")
        print(f"{Colors.WHITE}🔄 Status: {docs_response.status_code}{Colors.END}")
        if docs_response.status_code == 200:
            print_success("Documentación Swagger accesible")
            print_info("🌐 Accede a: http://localhost:8000/docs")
        else:
            print_error(f"Error accediendo a docs - Status: {docs_response.status_code}")
    except Exception as e:
        print_error(f"Error en documentación: {e}")
    
    # ==========================================
    # 7. RESUMEN FINAL
    # ==========================================
    print_header("📊 RESUMEN DE PRUEBAS")
    
    # Obtener estadísticas finales
    if access_token:
        final_balance_response = test_endpoint("GET", "/api/wallet/balance", headers=auth_headers, expected_status=200)
        final_transactions_response = test_endpoint("GET", "/api/wallet/transactions", headers=auth_headers, expected_status=200)
        
        if final_balance_response and final_balance_response.status_code == 200:
            balance_data = final_balance_response.json()
            print_info(f"💰 Balance final: ${balance_data.get('balance', 0)}")
        
        if final_transactions_response and final_transactions_response.status_code == 200:
            trans_data = final_transactions_response.json()
            transactions = trans_data.get('transactions', [])
            print_info(f"📋 Total de transacciones: {len(transactions)}")
            
            # Contar por estado
            status_counts = {}
            for trans in transactions:
                status = trans.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print_info(f"   - {status}: {count}")
    
    print_success("🎉 Todas las pruebas completadas!")
    print_info("🌐 Documentación disponible en: http://localhost:8000/docs")
    print_info("📊 API Health Check: http://localhost:8000/openapi.json")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n💥 Error inesperado: {e}")
        sys.exit(1)
