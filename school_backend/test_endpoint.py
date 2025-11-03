"""
Script de prueba para verificar endpoints y diagnosticar errores.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, token=None):
    """Prueba un endpoint y muestra el resultado."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            if endpoint == "/api/auth/login":
                response = requests.post(url, data=data, headers=headers)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, json=data, headers=headers)
        else:
            response = requests.request(method.upper(), url, json=data, headers=headers)
        
        print(f"\n{'='*60}")
        print(f"{method.upper()} {endpoint}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response (text): {response.text}")
        
        return response
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: No se pudo conectar al servidor en {BASE_URL}")
        print("   Asegúrate de que el servidor esté ejecutándose.")
        return None
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 Pruebas de Endpoints del Sistema Escolar\n")
    
    # Probar endpoints básicos
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/docs")
    
    print("\n" + "="*60)
    print("Para probar endpoints protegidos, necesitas un token.")
    print("Primero registra un usuario en /api/auth/register")
    print("Luego inicia sesión en /api/auth/login para obtener el token.")
    print("="*60)

