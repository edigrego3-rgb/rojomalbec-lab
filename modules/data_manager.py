# modules/data_manager.py
import streamlit as st
import pandas as pd
import gspread
from modules.conversions import convertir_a_base

# ============================================
# 2. GESTIÓN DE DATOS Y LÓGICA (GOOGLE SHEETS)
# ============================================

SHEET_NAME = "RojoMalbec DB"

# Definición de columnas y tipos
# AQUI ESTA EL CAMBIO: Agregué "Markup_Propio_Pct" a la lista de recetas
FILES = {
    "ingredientes": {"cols": {"Id": float, "Nombre": str, "Unidad_Base": str, "Categoria": str, "Costo": float, "Ultimo_Proveedor": str}},
    "recetas":      {"cols": {
        "Id": float, "Nombre": str, "Codigo": str, "Base_g": float, "Gramaje_Venta": float, "Tecnica": str, 
        "Precio_Venta": float, "Precio_Mayorista": float,
        "Margen_Fabrica_Pct": float, "Gastos_Fijos_Pct": float, "IIBB_Pct": float, "IVA_Pct": float,
        "Markup_Minorista": float, "Markup_Mayorista": float, "Markup_Revendedor": float,
        "Markup_Propio_Pct": float, "Descripcion": str
    }},
    "recetas_det":  {"cols": {"Id_Receta": float, "Ingrediente": str, "Cantidad": float, "Unidad_Consumo": str}},
    "proveedores":  {"cols": {"Id": float, "Nombre": str, "CUIT": str}},
    "clientes":     {"cols": {"Id": float, "Nombre": str, "CUIT": str, "Direccion": str, "Localidad": str, "Telefono": str}},
    "stock_log":    {"cols": {"UUID": str, "Ingrediente": str, "Cantidad": float, "Unidad_Base": str, "Tipo_Movimiento": str, "Costo_Real": float, "Proveedor": str, "Lote_Proveedor": str, "Fecha_Vencimiento": str, "Fecha_Movimiento": str}},
    "lotes_produccion": {"cols": {"Lote_Produccion": str, "Id_Receta": float, "Producto": str, "Kilos_Producidos": float, "Cantidad_Envases": float, "Gramaje_Por_Envase": float, "Costo_Total_MateriaPrima": float, "Costo_Unitario_KG": float, "Fecha_Produccion": str}},
    "lotes_produccion_det": {"cols": {"Lote_Produccion": str, "Ingrediente": str, "Cantidad_Usada": float, "Unidad_Base": str, "Lote_Proveedor": str, "Fecha_Vencimiento": str}},
    "ventas": {"cols": {"UUID": str, "Lote_Produccion": str, "Cliente": str, "Forma_Pago": str, "Cantidad_Vendida_KG": float, "Precio_Venta_Unitario_KG": float, "Precio_Total": float, "Ganancia_Neta": float, "Fecha_Venta": str}},
}

def get_connection():
    """Establece conexión con Google Sheets usando st.secrets"""
    if "gsheets_conn" not in st.session_state:
        try:
            creds_dict = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
            }
            gc = gspread.service_account_from_dict(creds_dict)
            st.session_state["gsheets_conn"] = gc
        except Exception as e:
            err_msg = str(e)
            if "getaddrinfo failed" in err_msg or "NameResolutionError" in err_msg:
                st.error("📡 **Error de Conexión:** No se pudo conectar con los servidores de Google. Verificá tu conexión a internet o el estado de tu señal de red.")
            elif "RemoteDisconnected" in err_msg:
                st.error("🔌 **Error de Red:** La conexión fue cerrada repentinamente por el servidor. Puede ser un micro-corte de internet.")
            else:
                st.error(f"❌ **Error de Conexión:** {e}")
            return None
    return st.session_state["gsheets_conn"]

def get_worksheet(gc, tab_name):
    """Obtiene una hoja de trabajo específica, creándola si no existe"""
    try:
        sh = gc.open(SHEET_NAME)
        try:
            return sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            # Crear si no existe
            return sh.add_worksheet(title=tab_name, rows=100, cols=20)
    except Exception as e:
        err_msg = str(e)
        if "getaddrinfo failed" in err_msg or "NameResolutionError" in err_msg:
            st.error("📡 **Error de Red:** No se pudieron descargar los datos de la nube. Verificá si tenés internet activo.")
        else:
            st.error(f"Error abriendo hoja {SHEET_NAME}: {e}")
        return None

def load_data(key):
    gc = get_connection()
    if not gc:
        return pd.DataFrame(columns=FILES[key]["cols"].keys())
    
    ws = get_worksheet(gc, key)
    cols_schema = FILES[key]["cols"]
    try:
        # 1. Obtener TODO de la hoja de forma cruda (get_all_values es lo más estable)
        raw_data = ws.get_all_values()
        if not raw_data:
            return pd.DataFrame(columns=cols_schema.keys())
            
        # 2. Extraer y limpiar cabeceras
        headers = [str(h).strip() for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        # 3. Mapear al esquema oficial (ignorar columnas fantasma como las de los índices)
        df_final = pd.DataFrame()
        for col, dtype in cols_schema.items():
            if col in df.columns:
                series = df[col].copy()
                if dtype in [float, int]:
                    # Limpieza vital: Convertir comas argentinas a puntos y quitar basura
                    series = series.astype(str).str.replace(',', '.', regex=False).str.strip()
                    # Convertir a número, los errores pasan a ser 0.0
                    df_final[col] = pd.to_numeric(series, errors='coerce').fillna(0.0).astype(float).round(2)
                else:
                    df_final[col] = series.fillna("").astype(str).str.strip()
            else:
                # Si falta la columna en la sheet, la creamos con valores por defecto
                defaults = {
                    "Margen_Fabrica_Pct": 43.0,
                    "Gastos_Fijos_Pct": 35.0,
                    "IIBB_Pct": 3.5,
                    "IVA_Pct": 21.0,
                    "Markup_Minorista": 65.0,
                    "Markup_Mayorista": 25.0,
                    "Markup_Revendedor": 50.0,
                    "Markup_Propio_Pct": 0.0 # Agregado default para la nueva columna
                }
                if col in defaults:
                    df_final[col] = defaults[col]
                else:
                    df_final[col] = 0.0 if dtype in [float, int] else ""

        # 4. Deduplicación por ID (Recetas) - Mantenemos la última versión
        if key == "recetas" and not df_final.empty and "Id" in df_final.columns:
            df_final["Id"] = pd.to_numeric(df_final["Id"], errors='coerce').fillna(0)
            df_final = df_final.sort_values("Id").drop_duplicates("Id", keep='last')

        return df_final
    except Exception as e:
        # En caso de error crítico, devolvemos un DF vacío con las columnas correctas
        return pd.DataFrame(columns=cols_schema.keys())

def save_data(key, df):
    # 0. Asegurar Esquema antes de Guardar
    if key in FILES:
        # Asegurar que las columnas existan y tengan el tipo correcto
        for col, dtype in FILES[key]["cols"].items():
            if col not in df.columns:
                df[col] = pd.Series(dtype=dtype).fillna(0.0 if dtype in [float, int] else "")
            try:
                if dtype in [float, int]:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(dtype)
                else:
                    df[col] = df[col].astype(dtype)
            except:
                pass

    # 1. Actualizar estado local (optimistic update)
    st.session_state[key] = df
    
    # 2. Actualizar Google Sheets
    gc = get_connection()
    if gc:
        ws = get_worksheet(gc, key)
        if ws:
            try:
                # Reemplazar NaN con "" para JSON
                df_to_upload = df.copy().fillna("")
                
                # --- LIMPIEZA QUIRÚRGICA: Solo subir las columnas del esquema ---
                official_cols = list(FILES[key]["cols"].keys())
                df_to_upload = df_to_upload[official_cols]

                ws.clear()
                # Usamos encabezados limpios
                data_list = [df_to_upload.columns.values.tolist()] + df_to_upload.values.tolist()
                
                # Subida en crudo (RAW) para evitar que Google interprete cosas raras
                ws.update(data_list, value_input_option='RAW')
                
            except Exception as e:
                st.error(f"Error guardando {key} en Cloud: {e}")

def init_data():
    """Carga inicial de datos en session_state"""
    if "data_loaded" not in st.session_state:
        with st.spinner('Conectando a la nube y descargando datos...'):
            for k in FILES.keys():
                st.session_state[k] = load_data(k)
            st.session_state["data_loaded"] = True

def get_df(key): 
    return st.session_state[key]

# --- LÓGICA DE NEGOCIO (Sin Cambios) ---

def calcular_stock_actual(df_stock_log, df_ingredientes):
    """Calcula Stock Actual y Costo Promedio Ponderado (CPP)."""
    
    if df_stock_log.empty:
        df_final = df_ingredientes[['Nombre', 'Unidad_Base']].rename(columns={'Nombre': 'Ingrediente'})
        df_final['Stock_Actual'] = 0.0
        df_final['Costo_Ponderado'] = 0.0
        return df_final

    # --- NUEVO MOTOR DE CÁLCULO: ÚLTIMO PRECIO FIJO (INGREDIENTE DIRECTO) ---
    # En este modelo, el Costo NO se calcula desde el Log.
    # El Costo es un atributo del Ingrediente (df_ingredientes['Costo']).
    # El Stock Log solo se usa para calcular la CANTIDAD actual.
    
    # 1. Calcular Cantidades (Sumar Entradas/Salidas)
    # Agrupamos por ingrediente y sumamos cantidad
    if not df_stock_log.empty:
        stock_sums = df_stock_log.groupby("Ingrediente")["Cantidad"].sum().to_dict()
    else:
        stock_sums = {}

    # 2. Construir DataFrame Resultado usando df_ingredientes como base maestra
    results = []
    
    for _, row in df_ingredientes.iterrows():
        ing = row['Nombre']
        unidad_base = row['Unidad_Base']
        costo_fijo = float(row.get('Costo', 0.0)) # El precio maestro
        
        qty_final = stock_sums.get(ing, 0.0)
        
        # Corrección de errores de punto flotante
        if abs(qty_final) < 0.0001:
            qty_final = 0.0
            
        # El "Costo Ponderado" para el reporte ahora es simplemente el Costo Fijo
        results.append({
            'Ingrediente': ing,
            'Unidad_Base': unidad_base,
            'Stock_Actual': round(qty_final, 3),
            'Costo_Ponderado': round(costo_fijo, 4), 
            'Proveedor': row.get('Ultimo_Proveedor', 'N/A'),
            'Total_Qty_In': qty_final # Mantener compatibilidad pero ya no se usa para ponderar
        })

    df_stock_final = pd.DataFrame(results)
    
    return df_stock_final[['Ingrediente', 'Unidad_Base', 'Stock_Actual', 'Costo_Ponderado', 'Proveedor', 'Total_Qty_In']]

def calcular_stock_por_lote(df_stock_log, df_ingredientes):
    """
    Calcula el stock remanente desglosado por cada entrada (lote/vencimiento).
    Usa una lógica FIFO simple para consumir las entradas con las salidas.
    """
    if df_stock_log.empty:
        return pd.DataFrame()

    # 1. Preparar datos
    df = df_stock_log.copy()
    df['Fecha_Movimiento'] = pd.to_datetime(df['Fecha_Movimiento'], errors='coerce')
    df = df.sort_values(['Ingrediente', 'Fecha_Movimiento', 'UUID'])

    # 2. Separar Entradas y Salidas
    entradas = df[df['Cantidad'] > 0].copy()
    salidas = df[df['Cantidad'] < 0].copy()
    
    # Columna para registrar cuánto queda de cada entrada
    entradas['Stock_Remanente'] = entradas['Cantidad']

    # 3. Consumir entradas con salidas (FIFO por ingrediente)
    for ingrediente in salidas['Ingrediente'].unique():
        ing_salidas = salidas[salidas['Ingrediente'] == ingrediente]
        ing_entradas = entradas[entradas['Ingrediente'] == ingrediente]
        
        total_a_descontar = abs(ing_salidas['Cantidad'].sum())
        
        for idx in ing_entradas.index:
            if total_a_descontar <= 0:
                break
            
            disponible = entradas.at[idx, 'Stock_Remanente']
            if disponible <= total_a_descontar:
                total_a_descontar -= disponible
                entradas.at[idx, 'Stock_Remanente'] = 0.0
            else:
                entradas.at[idx, 'Stock_Remanente'] = disponible - total_a_descontar
                total_a_descontar = 0.0

    # 4. Filtrar solo entradas con stock remanente > 0
    df_res = entradas[entradas['Stock_Remanente'] > 0.001].copy()
    
    # 5. Enriquecer con Precio Maestro y Proveedor (opcional, ya lo tiene el log pero df_i es la verdad actual)
    # Sin embargo, el log tiene el proveedor original de esa compra, lo cual es mejor para trazabilidad.
    
    # Unir con Unidad_Base de ingredientes
    df_res = df_res.merge(df_ingredientes[['Nombre', 'Costo', 'Ultimo_Proveedor']], left_on='Ingrediente', right_on='Nombre', how='left')
    
    # El precio unitario para valorizar es el Costo Fijo actual
    df_res['Precio_Unitario'] = df_res['Costo']
    df_res['Valor_Total'] = df_res['Stock_Remanente'] * df_res['Precio_Unitario']
    
    # Renombrar para claridad
    df_res = df_res.rename(columns={
        'Stock_Remanente': 'Cantidad_Stock',
        'Lote_Proveedor': 'Lote_Factura',
        'Ultimo_Proveedor': 'Proveedor_Maestro'
    })
    
    # Limpiar columnas
    cols_ok = ['Ingrediente', 'Unidad_Base', 'Cantidad_Stock', 'Precio_Unitario', 'Valor_Total', 'Lote_Factura', 'Fecha_Vencimiento', 'Fecha_Movimiento']
    return df_res[cols_ok].sort_values(['Ingrediente', 'Fecha_Vencimiento'])

def calculate_recipe_cost_per_kg(rid, df_r, df_rd, df_i, cpp_map_input):
    """Calcula el costo por kg de una receta específica usando un mapa de CPP (real o simulado)."""
    
    r_data = df_r[df_r["Id"] == rid].iloc[0]
    base_g = r_data["Base_g"]
    
    target_g = 1000.0 # Objetivo: calcular el costo de 1kg (1000g)
    if base_g == 0:
        return 0.0, pd.DataFrame(columns=['Ingrediente', 'Cantidad_BASE_SUMA', 'Costo_Unitario', 'Costo Estimado Total (CPP)'])
    
    factor = target_g / base_g
    detalles_base = df_rd[df_rd["Id_Receta"] == rid]
    
    costo_total_receta = 0.0
    detalles_costo = []
    
    for _, req in detalles_base.iterrows():
        ingrediente = req["Ingrediente"]
        unidad_receta = str(req["Unidad_Consumo"]).lower().strip()

        # Excluir packaging (unidades) del cálculo de costo MP, consistente con produccion.py
        if unidad_receta == 'unidades':
            continue

        cantidad_requerida = req["Cantidad"] * factor
        cantidad_base_suma = convertir_a_base(cantidad_requerida, unidad_receta)
        
        # Usar el CPP del mapa (puede ser real o simulado)
        costo_unitario_cpp = cpp_map_input.get(ingrediente, 0.0)
        costo_item = cantidad_base_suma * costo_unitario_cpp
        costo_total_receta += costo_item
        
        # Preparar detalle para el reporte
        unidad_base_stock = df_i[df_i["Nombre"] == ingrediente]["Unidad_Base"].iloc[0].lower()
        
        detalles_costo.append({
            'Ingrediente': ingrediente,
            'Cantidad_BASE_SUMA': cantidad_base_suma,
            'Costo_Unitario': costo_unitario_cpp,
            'Costo Estimado Total (CPP)': costo_item,
            'Unidad_Base_Stock': unidad_base_stock 
        })
        
    df_detalles = pd.DataFrame(detalles_costo)
    
    # Costo por KG es el Costo Total de los 1000g
    costo_unitario_kg = costo_total_receta / (target_g / 1000.0)
    
    return costo_unitario_kg, df_detalles

def consumir_stock_fifo(ingrediente, cantidad_requerida, df_stock_log):
    """
    Consume stock de un ingrediente usando FIFO y retorna el detalle de qué lotes se usaron.
    
    Args:
        ingrediente: Nombre del ingrediente
        cantidad_requerida: Cantidad a consumir (en unidad base)
        df_stock_log: DataFrame del stock_log actual
    
    Returns:
        list: Lista de diccionarios con {Lote_Proveedor, Cantidad_Usada, Fecha_Vencimiento}
    """
    if df_stock_log.empty:
        return []
    
    # Filtrar entradas de este ingrediente
    df = df_stock_log.copy()
    df['Fecha_Movimiento'] = pd.to_datetime(df['Fecha_Movimiento'], errors='coerce')
    df = df.sort_values(['Fecha_Movimiento'])
    
    # Separar entradas y salidas
    entradas = df[(df['Ingrediente'] == ingrediente) & (df['Cantidad'] > 0)].copy()
    salidas = df[(df['Ingrediente'] == ingrediente) & (df['Cantidad'] < 0)].copy()
    
    # Calcular stock remanente por lote
    entradas['Stock_Remanente'] = entradas['Cantidad']
    
    # Aplicar salidas anteriores
    total_salidas_previas = abs(salidas['Cantidad'].sum())
    for idx in entradas.index:
        if total_salidas_previas <= 0:
            break
        disponible = entradas.at[idx, 'Stock_Remanente']
        if disponible <= total_salidas_previas:
            total_salidas_previas -= disponible
            entradas.at[idx, 'Stock_Remanente'] = 0.0
        else:
            entradas.at[idx, 'Stock_Remanente'] = disponible - total_salidas_previas
            total_salidas_previas = 0.0
    
    # Ahora consumir la cantidad requerida y registrar de qué lotes sale
    lotes_usados = []
    restante = cantidad_requerida
    
    for idx in entradas.index:
        if restante <= 0:
            break
        
        disponible = entradas.at[idx, 'Stock_Remanente']
        if disponible <= 0:
            continue
            
        lote = entradas.at[idx, 'Lote_Proveedor']
        vencimiento = entradas.at[idx, 'Fecha_Vencimiento']
        unidad = entradas.at[idx, 'Unidad_Base']
        
        if disponible <= restante:
            # Usamos todo este lote
            lotes_usados.append({
                'Lote_Proveedor': lote,
                'Cantidad_Usada': disponible,
                'Unidad_Base': unidad,
                'Fecha_Vencimiento': vencimiento
            })
            restante -= disponible
        else:
            # Usamos parcialmente este lote
            lotes_usados.append({
                'Lote_Proveedor': lote,
                'Cantidad_Usada': restante,
                'Unidad_Base': unidad,
                'Fecha_Vencimiento': vencimiento
            })
            restante = 0
    
    return lotes_usados

def prepare_inkjet_export(df_prod):
    """
    Genera el contenido de un archivo de texto (.txt) para la impresora Asjet.
    Formato:
    PRODUCTO: [NOMBRE]
    RNE: 04006325 - RNPA E/T.
    LOTE:[ID_LOTE]
    Elab: MM/YYYY
    Vto. MM/YYYY
    """
    if df_prod.empty:
        return ""
    
    import re
    lines = []
    for _, row in df_prod.iterrows():
        # 1. Obtener fecha (con fallbacks)
        fecha_dt = pd.to_datetime(row['Fecha_Produccion'], dayfirst=True, errors='coerce')
        if pd.isna(fecha_dt):
            match = re.search(r'[- ](\d{2})(\d{2})(\d{2})$', str(row['Lote_Produccion']))
            if match:
                yy, mm, dd = match.groups()
                try: fecha_dt = pd.to_datetime(f"20{yy}-{mm}-{dd}")
                except: fecha_dt = pd.Timestamp.now().normalize()
            else:
                fecha_dt = pd.Timestamp.now().normalize()
        
        venc_dt = fecha_dt + pd.DateOffset(months=12)
        
        # 2. Construir el bloque con el nombre arriba como título (Pedido por usuario)
        lines.append(f"--- {row['Producto']} ---")
        lines.append("RNE: 04006325 - RNPA E/T.")
        lines.append(f"LOTE:{row['Lote_Produccion']}")
        lines.append(f"Elab: {fecha_dt.strftime('%m/%Y')}")
        lines.append(f"Vto. {venc_dt.strftime('%m/%Y')}")
        lines.append("-" * 20) # Separador visual
        lines.append("") # Línea en blanco entre lotes
        
    return "\n".join(lines)
