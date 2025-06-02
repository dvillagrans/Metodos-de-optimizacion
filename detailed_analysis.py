import requests
import json

def analyze_problem_detailed():
    """Análisis detallado del problema y prueba con diferentes métodos"""
    print("🔍 ANÁLISIS DETALLADO DEL PROBLEMA")
    print("=" * 50)
    
    # Primero, analicemos la región factible del problema
    print("📊 REGIÓN FACTIBLE:")
    print("Restricciones:")
    print("  1) x₁ + x₂ + x₃ ≤ 30")
    print("  2) 2x₁ + x₂ ≥ 40") 
    print("  3) 3x₂ + 2x₃ ≤ 60")
    print("  4) x₁, x₂, x₃ ≥ 0")
    print()
    
    # Veamos si el problema es factible
    print("🧮 VERIFICACIÓN DE FACTIBILIDAD:")
    
    # Punto candidato 1: x₁ = 20, x₂ = 0, x₃ = 0
    x1, x2, x3 = 20, 0, 0
    print(f"Punto 1: x₁={x1}, x₂={x2}, x₃={x3}")
    print(f"  Restricción 1: {x1} + {x2} + {x3} = {x1+x2+x3} ≤ 30? {x1+x2+x3 <= 30}")
    print(f"  Restricción 2: 2({x1}) + {x2} = {2*x1+x2} ≥ 40? {2*x1+x2 >= 40}")
    print(f"  Restricción 3: 3({x2}) + 2({x3}) = {3*x2+2*x3} ≤ 60? {3*x2+2*x3 <= 60}")
    print(f"  Z = 2({x1}) + 3({x2}) + 4({x3}) = {2*x1+3*x2+4*x3}")
    print()
    
    # Punto candidato 2: x₁ = 10, x₂ = 20, x₃ = 0  
    x1, x2, x3 = 10, 20, 0
    print(f"Punto 2: x₁={x1}, x₂={x2}, x₃={x3}")
    print(f"  Restricción 1: {x1} + {x2} + {x3} = {x1+x2+x3} ≤ 30? {x1+x2+x3 <= 30}")
    print(f"  Restricción 2: 2({x1}) + {x2} = {2*x1+x2} ≥ 40? {2*x1+x2 >= 40}")
    print(f"  Restricción 3: 3({x2}) + 2({x3}) = {3*x2+2*x3} ≤ 60? {3*x2+2*x3 <= 60}")
    print(f"  Z = 2({x1}) + 3({x2}) + 4({x3}) = {2*x1+3*x2+4*x3}")
    print()
    
    # Punto candidato 3: Tratemos de maximizar x₃
    x1, x2, x3 = 0, 0, 30
    print(f"Punto 3: x₁={x1}, x₂={x2}, x₃={x3}")
    print(f"  Restricción 1: {x1} + {x2} + {x3} = {x1+x2+x3} ≤ 30? {x1+x2+x3 <= 30}")
    print(f"  Restricción 2: 2({x1}) + {x2} = {2*x1+x2} ≥ 40? {2*x1+x2 >= 40}")
    print(f"  Restricción 3: 3({x2}) + 2({x3}) = {3*x2+2*x3} ≤ 60? {3*x2+2*x3 <= 60}")
    print(f"  Z = 2({x1}) + 3({x2}) + 4({x3}) = {2*x1+3*x2+4*x3}")
    print()
    
    # El punto 3 no es factible, así que el problema necesita una solución más compleja
    
    print("🔧 PROBANDO DIFERENTES MÉTODOS:")
    
    # Test 1: Método Simplex regular (no Dos Fases)
    print("\n1️⃣ Probando método Simplex regular...")
    test_simplex_regular()
    
    # Test 2: Problema modificado para Dos Fases
    print("\n2️⃣ Probando Dos Fases con problema bien formulado...")
    test_dosfases_modified()
    
    # Test 3: Verificar si el problema es realmente no factible
    print("\n3️⃣ Verificando factibilidad...")
    check_feasibility()

def test_simplex_regular():
    """Test con método simplex regular"""
    # Para simplex regular, necesitamos convertir a forma estándar manualmente
    # x₁ + x₂ + x₃ + s₁ = 30
    # 2x₁ + x₂ - s₂ = 40  (nota: -s₂ porque es ≥)
    # 3x₂ + 2x₃ + s₃ = 60
    
    url = 'http://localhost:5000/api/resolver/simplex'
    
    # Incluir variables de holgura/exceso en la matriz A
    api_data = {
        'c': [2, 3, 4, 0, 0, 0],  # Incluir coeficientes para s₁, s₂, s₃
        'A': [
            [1, 1, 1, 1, 0, 0],    # x₁ + x₂ + x₃ + s₁ = 30
            [2, 1, 0, 0, -1, 0],   # 2x₁ + x₂ - s₂ = 40
            [0, 3, 2, 0, 0, 1]     # 3x₂ + 2x₃ + s₃ = 60
        ],
        'b': [30, 40, 60],
        'minimize': False,
        'track_iterations': True
    }
    
    try:
        response = requests.post(
            url, 
            json=api_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Estado: {result.get('success', 'Unknown')}")
            solution = result.get('solution', [])
            if len(solution) >= 3:
                print(f"   Solución (x₁,x₂,x₃): [{solution[0]:.3f}, {solution[1]:.3f}, {solution[2]:.3f}]")
                print(f"   Valor óptimo: {result.get('optimal_value', 'N/A')}")
            else:
                print(f"   Solución completa: {solution}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error: {e}")

def test_dosfases_modified():
    """Test Dos Fases con formulación correcta"""
    url = 'http://localhost:5000/api/resolver/dosfases'
    
    # Para Dos Fases, la restricción ≥ se maneja internamente
    api_data = {
        'c': [2, 3, 4],
        'A': [
            [1, 1, 1],    # x₁ + x₂ + x₃ ≤ 30
            [2, 1, 0],    # 2x₁ + x₂ ≥ 40 (se manejará internamente)
            [0, 3, 2]     # 3x₂ + 2x₃ ≤ 60
        ],
        'b': [30, 40, 60],
        'eq_constraints': [1],  # Restricción 2 es ≥, por lo que necesita manejo especial
        'minimize': False,
        'track_iterations': True
    }
    
    try:
        response = requests.post(
            url, 
            json=api_data, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Estado: {result.get('success', 'Unknown')}")
            print(f"   Solución: {result.get('solution', 'N/A')}")
            print(f"   Valor óptimo: {result.get('optimal_value', 'N/A')}")
            print(f"   Iteraciones: {len(result.get('tableau_history', []))}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   💥 Error: {e}")

def check_feasibility():
    """Verificar si el problema es factible usando análisis gráfico"""
    print("   📐 Análisis gráfico de factibilidad:")
    print("   • La restricción 2x₁ + x₂ ≥ 40 define una región")
    print("   • La restricción x₁ + x₂ + x₃ ≤ 30 limita la suma total")
    print("   • Para que sea factible, necesitamos encontrar puntos que satisfagan ambas")
    print()
    
    # Busquemos puntos en la frontera
    print("   🎯 Puntos en la frontera:")
    for x3 in [0, 10, 20]:
        max_x1_x2 = 30 - x3
        if max_x1_x2 >= 0:
            # Para 2x₁ + x₂ = 40, necesitamos ver si podemos hacerlo con x₁ + x₂ ≤ max_x1_x2
            print(f"   • Con x₃ = {x3}: x₁ + x₂ ≤ {max_x1_x2}")
            
            # Si x₂ = 0, entonces 2x₁ = 40, so x₁ = 20
            if 20 <= max_x1_x2:
                x1, x2 = 20, 0
                z = 2*x1 + 3*x2 + 4*x3
                print(f"     - Solución factible: x₁={x1}, x₂={x2}, x₃={x3}, Z={z}")
                
            # Si x₁ = 0, entonces x₂ = 40
            if 40 <= max_x1_x2:
                x1, x2 = 0, 40
                z = 2*x1 + 3*x2 + 4*x3
                print(f"     - Solución factible: x₁={x1}, x₂={x2}, x₃={x3}, Z={z}")
                
            # Punto en la frontera x₁ + x₂ = max_x1_x2
            # 2x₁ + x₂ = 40 y x₁ + x₂ = max_x1_x2
            # Resolviendo: x₁ = 40 - max_x1_x2, x₂ = 2*max_x1_x2 - 40
            if max_x1_x2 >= 40:
                continue
            x1 = 40 - max_x1_x2
            x2 = 2*max_x1_x2 - 40
            if x1 >= 0 and x2 >= 0:
                z = 2*x1 + 3*x2 + 4*x3
                print(f"     - Frontera: x₁={x1}, x₂={x2}, x₃={x3}, Z={z}")

if __name__ == "__main__":
    analyze_problem_detailed()
