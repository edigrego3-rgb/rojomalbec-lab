
# modules/nutrition.py
import pandas as pd
import unicodedata

# Perfiles Nutricionales por categoría (por 100g)
# Estos perfiles se aplicarán si el ingrediente contiene la palabra clave.
NUTRITION_PROFILES = {
    "te negro": {"Humedad": 8.0, "Proteinas": 15.0, "Grasas": 1.0, "Carbohidratos": 50.0, "Cenizas": 6.0},
    "te rojo": {"Humedad": 8.0, "Proteinas": 20.0, "Grasas": 2.5, "Carbohidratos": 45.0, "Cenizas": 5.0},
    "te verde": {"Humedad": 7.0, "Proteinas": 22.0, "Grasas": 2.0, "Carbohidratos": 40.0, "Cenizas": 5.5},
    "azucar": {"Humedad": 0.5, "Proteinas": 0.0, "Grasas": 0.0, "Carbohidratos": 99.5, "Cenizas": 0.0},
    "canela": {"Humedad": 10.0, "Proteinas": 4.0, "Grasas": 1.2, "Carbohidratos": 80.0, "Cenizas": 2.5},
    "jengibre": {"Humedad": 10.0, "Proteinas": 9.0, "Grasas": 6.0, "Carbohidratos": 70.0, "Cenizas": 5.0},
    "menta": {"Humedad": 8.0, "Proteinas": 19.0, "Grasas": 6.0, "Carbohidratos": 52.0, "Cenizas": 12.0},
    "arandanos": {"Humedad": 15.0, "Proteinas": 0.1, "Grasas": 1.4, "Carbohidratos": 82.0, "Cenizas": 0.5},
    "hibiscus": {"Humedad": 10.0, "Proteinas": 2.0, "Grasas": 0.0, "Carbohidratos": 7.0, "Cenizas": 7.0},
    "rosa mosqueta": {"Humedad": 10.0, "Proteinas": 1.6, "Grasas": 0.5, "Carbohidratos": 38.0, "Cenizas": 5.0},
    "anis": {"Humedad": 9.0, "Proteinas": 18.0, "Grasas": 15.0, "Carbohidratos": 50.0, "Cenizas": 5.0},
    "ajo": {"Humedad": 6.0, "Proteinas": 16.0, "Grasas": 0.5, "Carbohidratos": 70.0, "Cenizas": 3.0},
    "cebolla": {"Humedad": 5.0, "Proteinas": 10.0, "Grasas": 0.4, "Carbohidratos": 80.0, "Cenizas": 4.0},
    "pimienta": {"Humedad": 12.0, "Proteinas": 10.0, "Grasas": 3.0, "Carbohidratos": 64.0, "Cenizas": 4.5},
    "pimenton": {"Humedad": 10.0, "Proteinas": 14.0, "Grasas": 13.0, "Carbohidratos": 54.0, "Cenizas": 6.0},
    "semillas": {"Humedad": 6.0, "Proteinas": 20.0, "Grasas": 50.0, "Carbohidratos": 20.0, "Cenizas": 4.0},
    "harina": {"Humedad": 12.0, "Proteinas": 10.0, "Grasas": 1.5, "Carbohidratos": 75.0, "Cenizas": 1.0},
    "hongo": {"Humedad": 10.0, "Proteinas": 20.0, "Grasas": 3.0, "Carbohidratos": 60.0, "Cenizas": 7.0},
    "sal": {"Humedad": 0.1, "Proteinas": 0.0, "Grasas": 0.0, "Carbohidratos": 0.0, "Cenizas": 99.0},
}

DEFAULT_VALUES = {"Humedad": 0.0, "Proteinas": 0.0, "Grasas": 0.0, "Carbohidratos": 0.0, "Cenizas": 0.0}

def normalize_text(text):
    """Elimina acentos y convierte a minúsculas para una búsqueda robusta."""
    if not isinstance(text, str): return ""
    text = text.lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_ingredient_nutrition(name):
    """Busca el perfil nutricional basado en palabras clave dentro del nombre."""
    norm_name = normalize_text(name)
    
    # 1. Intentar match por palabras clave priorizando las más largas
    # Ordenar por longitud descendente para que "te rojo" gane a "te"
    sorted_keywords = sorted(NUTRITION_PROFILES.keys(), key=len, reverse=True)
    
    for kw in sorted_keywords:
        if kw in norm_name:
            return NUTRITION_PROFILES[kw]
            
    return DEFAULT_VALUES

def calculate_recipe_composition(ingredients_list, total_mass_g):
    """Calcula la composición porcentual basada en la masa de cada componente."""
    if total_mass_g <= 0:
        return pd.DataFrame()

    totals = {"Humedad": 0.0, "Proteinas": 0.0, "Grasas": 0.0, "Carbohidratos": 0.0, "Cenizas": 0.0}
    
    for item in ingredients_list:
        nutri = get_ingredient_nutrition(item['Ingrediente'])
        mass_factor = item['Cantidad_g'] / 100.0
        
        for key in totals:
            totals[key] += nutri[key] * mass_factor
            
    report = []
    for key, val in totals.items():
        percentage = (val / total_mass_g) * 100
        # Limitar al 100% por errores menores de suma o base de datos
        percentage = min(percentage, 100.0)
        report.append({"Componente": key, "Valor (%)": round(percentage, 2)})
    
    return pd.DataFrame(report)
