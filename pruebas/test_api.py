#!/usr/bin/env python3
"""
Script de pruebas para la API de Ticket Payment
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
    "email": "test@example.com",
    "password": "password123",
    "payment_method": {
        "card_holder": "Usuario Test",
        "card_number": "1234567890123456",
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
    print(f"{Colors.WHITE}ℹ️  {message}{Colors.END}")

def print_response(response):
    """Imprime la respuesta de manera formateada"""
    try:
        data = response.json()
        print(f"{Colors.PURPLE}📄 Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}{Colors.END}")
    except:
        print(f"{Colors.PURPLE}📄 Respuesta: {response.text}{Colors.END}")

def test_endpoint(method, endpoint, data=None, headers=None, expected_status=200):
    """Función genérica para probar endpoints"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print_error(f"Método HTTP no soportado: {method}")
            return None
            
        print(f"{Colors.WHITE}📊 Status Code: {response.status_code}{Colors.END}")
        
        if response.status_code == expected_status:
            print_success(f"Test exitoso - Status: {response.status_code}")
            print_response(response)
            return response
        else:
            print_error(f"Test falló - Esperado: {expected_status}, Obtenido: {response.status_code}")
            print_response(response)
            return response
            
    except requests.exceptions.ConnectionError:
        print_error("No se pudo conectar al servidor. ¿Está ejecutándose la API?")
        return None
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        return None

def main():
    """Función principal que ejecuta todas las pruebas"""
    print_header("PRUEBAS DE API - TICKET PAYMENT SYSTEM")
    print_info(f"Iniciando pruebas en: {BASE_URL}")
    print_info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Variables para almacenar datos entre tests
    access_token = None
    user_id = None
    payment_method_id = None
    
    # Test 1: Verificar que el servidor esté funcionando
    print_test("Verificar servidor", "GET", "/")
    response = test_endpoint("GET", "/")
    if not response:
        print_error("El servidor no está disponible. Terminando pruebas.")
        return
    
    # Test 2: Registrar usuario
    print_test("Registrar usuario", "POST", "/api/register")
    response = test_endpoint("POST", "/api/register", data=TEST_USER, expected_status=200)
    if response and response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        user_id = data.get("user_id")
        print_info(f"Token obtenido: {access_token[:20]}...")
        print_info(f"User ID: {user_id}")
    
    # Test 3: Login con credenciales
    print_test("Login de usuario", "POST", "/api/login")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    response = test_endpoint("POST", "/api/login", data=login_data)
    if response and response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")  # Actualizar token
        print_info(f"Nuevo token obtenido: {access_token[:20]}...")
    
    # Test 4: Login con OAuth2 (form data)
    print_test("Login OAuth2", "POST", "/token")
    try:
        form_data = {
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = requests.post(f"{BASE_URL}/token", data=form_data)
        print(f"{Colors.WHITE}📊 Status Code: {response.status_code}{Colors.END}")
        if response.status_code == 200:
            print_success("Login OAuth2 exitoso")
            print_response(response)
        else:
            print_error(f"Login OAuth2 falló - Status: {response.status_code}")
            print_response(response)
    except Exception as e:
        print_error(f"Error en login OAuth2: {str(e)}")
    
    if not access_token:
        print_error("No se pudo obtener token de acceso. Terminando pruebas autenticadas.")
        return
    
    # Headers para requests autenticados
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 5: Obtener perfil de usuario
    print_test("Obtener perfil", "GET", "/api/user/profile")
    test_endpoint("GET", "/api/user/profile", headers=auth_headers)
    
    # Test 6: Obtener QR del usuario
    print_test("Obtener QR de usuario", "GET", "/api/user/qr")
    response = test_endpoint("GET", "/api/user/qr", headers=auth_headers)
    if response and response.status_code == 200:
        data = response.json()
        qr_data = data.get("qr_base64", "")
        print_info(f"QR generado (primeros 50 chars): {qr_data[:50]}...")
    
    # Test 7: Listar métodos de pago
    print_test("Listar métodos de pago", "GET", "/api/payment/methods")
    test_endpoint("GET", "/api/payment/methods", headers=auth_headers)
    
    # Test 8: Agregar método de pago
    print_test("Agregar método de pago", "POST", "/api/payment/methods")
    new_payment_method = {
        "card_holder": "Test User",
        "card_number": "9876543210987654",
        "expiry": "06/26",
        "cvv": "456"
    }
    response = test_endpoint("POST", "/api/payment/methods", data=new_payment_method, headers=auth_headers)
    if response and response.status_code == 200:
        data = response.json()
        payment_method_id = data.get("payment_method", {}).get("id")
        print_info(f"Método de pago agregado con ID: {payment_method_id}")
    
    # Test 9: Obtener balance de billetera
    print_test("Obtener balance", "GET", "/api/wallet")
    test_endpoint("GET", "/api/wallet", headers=auth_headers)
    
    # Test 10: Recargar billetera
    print_test("Recargar billetera", "POST", "/api/wallet/topup")
    topup_data = {
        "amount": 100.0,
        "payment_method_id": payment_method_id or "test-method-id"
    }
    test_endpoint("POST", "/api/wallet/topup", data=topup_data, headers=auth_headers)
    
    # Test 11: Realizar pago por QR
    print_test("Pago por QR", "POST", "/api/payment/scan")
    scan_data = {
        "qr_data": user_id or "test-qr-data",
        "amount": 25.0
    }
    test_endpoint("POST", "/api/payment/scan", data=scan_data, headers=auth_headers)
    
    # Test 12: Eliminar método de pago
    if payment_method_id:
        print_test("Eliminar método de pago", "DELETE", f"/api/payment/methods/{payment_method_id}")
        test_endpoint("DELETE", f"/api/payment/methods/{payment_method_id}", headers=auth_headers)
    else:
        print_test("Eliminar método de pago", "DELETE", "/api/payment/methods/test-id")
        test_endpoint("DELETE", "/api/payment/methods/test-id", headers=auth_headers, expected_status=404)
    
    # Test 13: Verificar balance final
    print_test("Balance final", "GET", "/api/wallet")
    test_endpoint("GET", "/api/wallet", headers=auth_headers)
    
    # PRUEBAS ESPECÍFICAS DE MÉTODOS DE PAGO
    test_payment_method_scenarios()
    
    # Resumen final
    print_header("RESUMEN DE PRUEBAS COMPLETADO")
    print_info("Todas las rutas de la API han sido probadas")
    print_info("Revisa los resultados arriba para verificar el funcionamiento")
    print_info(f"Pruebas completadas a las: {datetime.now().strftime('%H:%M:%S')}")

def test_payment_method_scenarios():
    """Pruebas específicas para escenarios de métodos de pago"""
    print_header("PRUEBAS ESPECÍFICAS DE MÉTODOS DE PAGO")
    print_info("Probando diferentes escenarios de manejo de métodos de pago")
    
    # Escenario 1: Usuario sin método de pago inicial
    test_scenario_no_payment_method()
    
    # Escenario 2: Usuario con método de pago inicial
    test_scenario_with_payment_method()

def test_scenario_no_payment_method():
    """Escenario: Usuario se registra sin método de pago, luego agrega uno"""
    print_header("ESCENARIO 1: REGISTRO SIN MÉTODO DE PAGO")
    
    # Datos del usuario sin método de pago
    user_data = {
        "name": "Usuario Sin Tarjeta",
        "email": f"sin_tarjeta_{int(time.time())}@example.com",  # Email único
        "password": "password123"
    }
    
    print_test("Registrando usuario sin método de pago", "POST", "/api/register")
    response = test_endpoint("POST", "/api/register", data=user_data)
    
    if not response or response.status_code != 200:
        print_error("Falló el registro del usuario sin método de pago")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verificar que no hay métodos de pago
    print_test("Verificando métodos de pago iniciales", "GET", "/api/payment/methods")
    response = test_endpoint("GET", "/api/payment/methods", headers=headers)
    
    if response and response.status_code == 200:
        methods = response.json()
        print_info(f"Métodos de pago encontrados: {len(methods)}")
        if len(methods) == 0:
            print_success("✅ Correcto: No hay métodos de pago iniciales")
        else:
            print_error(f"❌ Error: Se esperaban 0 métodos, se encontraron {len(methods)}")
    
    # Agregar primer método de pago
    print_test("Agregando primer método de pago", "POST", "/api/payment/methods")
    new_method = {
        "card_holder": "Usuario Sin Tarjeta",
        "card_number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123"
    }
    
    response = test_endpoint("POST", "/api/payment/methods", data=new_method, headers=headers)
    
    # Verificar métodos después de agregar
    print_test("Verificando métodos después de agregar", "GET", "/api/payment/methods")
    response = test_endpoint("GET", "/api/payment/methods", headers=headers)
    
    if response and response.status_code == 200:
        methods = response.json()
        print_info(f"Total de métodos después de agregar: {len(methods)}")
        if len(methods) == 1:
            print_success("✅ Correcto: Se agregó exactamente 1 método de pago")
            # Verificar que tiene ID
            if methods[0].get('id'):
                print_success("✅ Correcto: El método de pago tiene ID")
            else:
                print_error("❌ Error: El método de pago no tiene ID")
        else:
            print_error(f"❌ Error: Se esperaba 1 método, se encontraron {len(methods)}")

def test_scenario_with_payment_method():
    """Escenario: Usuario se registra con método de pago, luego agrega otro"""
    print_header("ESCENARIO 2: REGISTRO CON MÉTODO DE PAGO")
    
    # Datos del usuario con método de pago
    user_data = {
        "name": "Usuario Con Tarjeta",
        "email": f"con_tarjeta_{int(time.time())}@example.com",  # Email único
        "password": "password123",
        "payment_method": {
            "card_holder": "Usuario Con Tarjeta",
            "card_number": "5555555555554444",
            "expiry": "06/26",
            "cvv": "456"
        }
    }
    
    print_test("Registrando usuario con método de pago", "POST", "/api/register")
    response = test_endpoint("POST", "/api/register", data=user_data)
    
    if not response or response.status_code != 200:
        print_error("Falló el registro del usuario con método de pago")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verificar métodos iniciales
    print_test("Verificando métodos de pago iniciales", "GET", "/api/payment/methods")
    response = test_endpoint("GET", "/api/payment/methods", headers=headers)
    
    if response and response.status_code == 200:
        methods = response.json()
        print_info(f"Métodos de pago encontrados: {len(methods)}")
        if len(methods) == 1:
            print_success("✅ Correcto: Se encontró 1 método de pago inicial")
            # Verificar que tiene ID
            if methods[0].get('id'):
                print_success("✅ Correcto: El método inicial tiene ID")
            else:
                print_error("❌ Error: El método inicial no tiene ID")
        else:
            print_error(f"❌ Error: Se esperaba 1 método inicial, se encontraron {len(methods)}")
    
    # Agregar segundo método de pago
    print_test("Agregando segundo método de pago", "POST", "/api/payment/methods")
    new_method = {
        "card_holder": "Usuario Con Tarjeta",
        "card_number": "4000000000000002",
        "expiry": "03/27",
        "cvv": "789"
    }
    
    response = test_endpoint("POST", "/api/payment/methods", data=new_method, headers=headers)
    
    # Verificar métodos después de agregar segundo
    print_test("Verificando métodos después de agregar segundo", "GET", "/api/payment/methods")
    response = test_endpoint("GET", "/api/payment/methods", headers=headers)
    
    if response and response.status_code == 200:
        methods = response.json()
        print_info(f"Total de métodos después de agregar segundo: {len(methods)}")
        if len(methods) == 2:
            print_success("✅ Correcto: Se tienen exactamente 2 métodos de pago")
            # Verificar que ambos tienen ID
            ids_found = sum(1 for method in methods if method.get('id'))
            if ids_found == 2:
                print_success("✅ Correcto: Ambos métodos tienen ID")
            else:
                print_error(f"❌ Error: Solo {ids_found} de 2 métodos tienen ID")
        else:
            print_error(f"❌ Error: Se esperaban 2 métodos, se encontraron {len(methods)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Pruebas interrumpidas por el usuario{Colors.END}")
    except Exception as e:
        print_error(f"Error fatal en las pruebas: {str(e)}")
        sys.exit(1)
