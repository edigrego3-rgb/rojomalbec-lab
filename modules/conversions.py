
# modules/conversions.py
import pandas as pd

UNIDADES_CONSUMO = ["kg", "g", "ml", "unidades", "lt"]
UNIDADES_BASE = ["g", "ml", "unidades"]

def get_conversion_factor(from_unit, to_unit):
    """Obtiene el factor para convertir entre unidades de compra (ej: de g a kg, o de kg a g)."""
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()

    if from_unit == to_unit:
        return 1.0
    
    # Conversiones 1000x (de mayor a menor)
    if (from_unit == 'kg' and to_unit == 'g') or \
       (from_unit == 'lt' and to_unit == 'ml'):
        return 1000.0
        
    # Conversiones 1/1000x (de menor a mayor)
    if (from_unit == 'g' and to_unit == 'kg') or \
       (from_unit == 'ml' and to_unit == 'lt'):
        return 1/1000.0 
        
    # Conversiones a/desde unidades (debe ser 1:1, si no, hay error en el dato)
    if from_unit in ['unidades', 'unidad'] and to_unit in ['unidades', 'unidad']:
        return 1.0

    # Si hay una mezcla de unidades no compatibles (ej: kg a unidades), retorna 0 para evitar cálculo incorrecto.
    if from_unit != to_unit and ('unidades' in from_unit or 'unidades' in to_unit) or \
       (from_unit in ['kg','g'] and to_unit in ['lt','ml']) or \
       (from_unit in ['lt','ml'] and to_unit in ['kg','g']):
         return 0.0 
        
    return 1.0 # Factor de conversión predeterminado si no es una conversión conocida

def convertir_a_base(cantidad, unidad_consumo):
    """Convierte la cantidad de consumo (kg, lt) a la unidad base (g, ml)."""
    # Esta función ahora usa la nueva y más robusta get_conversion_factor
    base_unit = 'g' if unidad_consumo.lower().strip() in ['kg', 'g'] else \
                'ml' if unidad_consumo.lower().strip() in ['lt', 'ml'] else 'unidades'
             
    factor = get_conversion_factor(unidad_consumo, base_unit)
             
    return cantidad * factor

def ajustar_unidad_para_display(row):
    """
    Función de ajuste para display, originalmente diseñada para Pestaña 3,
    por eso espera 'Cantidad_BASE_SUMA' y 'Unidad_Base_Stock'.
    """
    cantidad = row['Cantidad_BASE_SUMA']
    unidad_stock = row['Unidad_Base_Stock'].lower()
    
    row['Cantidad_BASE_SUMA'] = round(cantidad, 3) 

    if unidad_stock == 'g' and cantidad >= 1000:
        row['Cantidad_BASE_SUMA'] = round(cantidad / 1000.0, 3)
        row['Unidad_Base_Stock'] = 'kg'
    elif unidad_stock == 'ml' and cantidad >= 1000:
        row['Cantidad_BASE_SUMA'] = round(cantidad / 1000.0, 3)
        row['Unidad_Base_Stock'] = 'lt'
    return row
