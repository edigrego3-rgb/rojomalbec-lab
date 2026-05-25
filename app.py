import streamlit as st
import pandas as pd
import os
import sys

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Priorizamos el directorio actual (importante para el despliegue en la nube)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# También mantenemos el relativo para ejecución local si fuera necesario
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from modules.data_manager import get_df, init_data, calcular_stock_actual, calculate_recipe_cost_per_kg
    from modules.conversions import convertir_a_base, UNIDADES_CONSUMO
except ImportError as e:
    st.error(f"❌ Error de Importación: {e}. Revisa las rutas de la App Lab.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Rojo Malbec Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INICIALIZACIÓN DE DATOS ---
init_data()

# --- ESTILO DARK MODE PREMIUM ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
    }
    .stButton>button {
        background-color: #8b0000;
        color: white;
        border-radius: 10px;
        border: none;
        width: 100%;
    }
    h1, h2, h3 {
        color: #d4af37;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        border-radius: 10px;
        color: white;
        padding: 10px 15px;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #8b0000;
    }
    div[data-testid="stMetricValue"] {
        color: #d4af37;
    }
    .recipe-card {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #8b0000;
        margin-bottom: 20px;
    }
    /* Optimización para móviles */
    @media (max-width: 600px) {
        .stTabs [data-baseweb="tab"] {
            padding: 8px 10px;
            font-size: 11px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (MODO ADMIN) ---
st.sidebar.title("🔐 Acceso")
admin_key = st.sidebar.text_input("Contraseña Administrador", type="password")
is_admin = (admin_key == "rojoadmin")

if is_admin:
    st.sidebar.success("✅ MODO ADMINISTRADOR")
else:
    st.sidebar.info("Modo Lectura")

# --- CABECERA ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("🧪 Rojo Malbec Lab")
    st.caption("Ingeniería de Sabor & Bitácora de Autor")
with col_h2:
    if st.button("🔄"):
        st.rerun()

# --- NAVEGACIÓN (Pestañas Finales) ---
tab_recetas, tab_mostrador, tab_insumos, tab_producido, tab_ventas = st.tabs([
    "📂 Recetas & Notas", 
    "🏷️ Mostrador",
    "🌿 Insumos", 
    "📦 Stock Prod.", 
    "📈 Ventas"
])

# --- MODULO RECETAS & NOTAS ---
with tab_recetas:
    df_r = get_df("recetas")
    df_rd = get_df("recetas_det")
    
    if not df_r.empty:
        receta_nom = st.selectbox("Elegir Blend", df_r["Nombre"].unique(), key="rec_select_main")
        r_data = df_r[df_r["Nombre"] == receta_nom].iloc[0]
        rid = r_data["Id"]
        
        col_card, col_tec = st.columns([1, 2])
        
        with col_card:
            st.markdown(f"""
            <div class='recipe-card'>
                <h2 style='color:white; margin:0;'>{receta_nom}</h2>
                <p style='color:#d4af37;'>{r_data.get('Codigo', 'S/C')}</p>
                <hr style='border-color:#333;'>
                <p><b>Base:</b> {r_data['Base_g']}g</p>
                <p><b>PVP Sugerido:</b> $ {r_data.get('Precio_Venta', 0):,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Notas específicas de esta receta
            st.markdown("#### 📝 Nota de Laboratorio")
            note_file = os.path.join(current_dir, f"nota_receta_{int(rid)}.txt")
            
            existing_note = ""
            if os.path.exists(note_file):
                with open(note_file, "r", encoding="utf-8") as f:
                    existing_note = f.read()
            
            new_note = st.text_area("Anotar idea para este blend:", value=existing_note, height=150, help="Ej: Subir 10% al mayorista de este producto.", key=f"note_area_{rid}")
            if st.button("💾 Guardar Nota", key=f"btn_save_note_{rid}"):
                with open(note_file, "w", encoding="utf-8") as f:
                    f.write(new_note)
                st.success("Nota guardada en el Lab.")
            
            # Ingredientes simple (expander)
            with st.expander("Ver Ingredientes"):
                detalles = df_rd[df_rd["Id_Receta"] == rid]
                st.table(detalles[['Ingrediente', 'Cantidad', 'Unidad_Consumo']])

        with col_tec:
            st.markdown("#### ⚙️ Protocolo & Fórmula (Edición)")
            tecnica_actual = r_data.get("Tecnica", "")
            
            if is_admin:
                # 1. Edición de Técnica
                nueva_tecnica = st.text_area("Editar Ritual (Admin):", 
                                          value=tecnica_actual if pd.notna(tecnica_actual) else "", 
                                          height=200)
                
                # 2. Edición de Ingredientes (Fórmula)
                st.markdown("#### 🧪 Ajustar Ingredientes de la Fórmula")
                detalles_actuales = df_rd[df_rd["Id_Receta"] == rid].copy()
                
                # Editor de tabla dinámico
                edited_detalles = st.data_editor(
                    detalles_actuales[['Ingrediente', 'Cantidad', 'Unidad_Consumo']],
                    column_config={
                        "Ingrediente": st.column_config.SelectboxColumn(options=get_df("ingredientes")["Nombre"].unique().tolist()), 
                        "Unidad_Consumo": st.column_config.SelectboxColumn(options=UNIDADES_CONSUMO)
                    },
                    key=f"editor_lab_{rid}",
                    num_rows="dynamic",
                    hide_index=True
                )
                
                if st.button("💾 GUARDAR CAMBIOS EN FÓRMULA (ERP)", type="primary"):
                    from modules.data_manager import save_data, load_data
                    
                    # Guardar Técnica
                    df_r_latest = load_data("recetas")
                    idx_r = df_r_latest[df_r_latest["Id"] == rid].index[0]
                    df_r_latest.at[idx_r, "Tecnica"] = nueva_tecnica
                    
                    # Guardar Ingredientes
                    df_rd_latest = load_data("recetas_det")
                    df_rd_clean = df_rd_latest[df_rd_latest["Id_Receta"] != rid]
                    
                    edited_detalles["Id_Receta"] = rid
                    # Limpiar nulos
                    edited_detalles = edited_detalles.dropna(subset=['Ingrediente', 'Cantidad'])
                    
                    df_rd_final = pd.concat([df_rd_clean, edited_detalles], ignore_index=True)
                    
                    # Recalcular Base_g
                    suma_g = sum(
                        convertir_a_base(row["Cantidad"], str(row["Unidad_Consumo"]).lower().strip())
                        for _, row in edited_detalles.iterrows()
                        if str(row["Unidad_Consumo"]).lower().strip() in ['g', 'kg']
                    )
                    if suma_g > 0:
                        df_r_latest.at[idx_r, "Base_g"] = suma_g
                    
                    # Guardar TODO en Drive
                    save_data("recetas", df_r_latest)
                    save_data("recetas_det", df_rd_final)
                    
                    st.success(f"✅ Fórmula y Ritual sincronizados. Nueva Base: {suma_g:.0f}g")
                    st.rerun()
            else:
                # Vista Lectura (Normal)
                if pd.notna(tecnica_actual) and tecnica_actual:
                    st.markdown(f"<div style='background:#1a1a1a; padding:15px; border-radius:10px; min-height:200px;'>{tecnica_actual}</div>", unsafe_allow_html=True)
                else:
                    st.info("Sin técnica definida.")
                
                st.markdown("#### 📋 Ingredientes")
                detalles = df_rd[df_rd["Id_Receta"] == rid]
                if not detalles.empty:
                    st.table(detalles[['Ingrediente', 'Cantidad', 'Unidad_Consumo']])
                else:
                    st.warning("Sin ingredientes.")

# --- MODULO MOSTRADOR (PRECIOS REALES) ---
with tab_mostrador:
    st.header("🏷️ Mostrador de Precios")
    st.caption("Valores actuales extraídos directamente de tu ERP.")
    
    if not df_r.empty:
        # Preparar tabla de precios
        df_mostrador = df_r[['Nombre', 'Precio_Venta', 'Precio_Mayorista', 'Base_g']].copy()
        df_mostrador.columns = ['Blend', 'PVP Sugerido (Venta)', 'Precio Mayorista', 'Gramos Base']
        
        # Filtro de búsqueda
        search_m = st.text_input("🔍 Buscar en mostrador...", key="search_mostrador")
        if search_m:
            df_mostrador = df_mostrador[df_mostrador["Blend"].str.contains(search_m, case=False)]
        
        st.dataframe(df_mostrador, hide_index=True, use_container_width=True)
        
        st.info("💡 Consejo: Usá el Administrador si necesitás modificar el gramaje de venta o el PVP desde la PC.")

# --- MODULO INSUMOS ---
with tab_insumos:
    st.header("🌿 Materias Primas")
    df_i = get_df("ingredientes")
    df_sl = get_df("stock_log")
    from modules.data_manager import calcular_stock_actual
    df_stock = calcular_stock_actual(df_sl, df_i)
    
    search_i = st.text_input("🔍 Buscar MP...", key="search_mp")
    if search_i:
        df_stock = df_stock[df_stock["Ingrediente"].str.contains(search_i, case=False)]
    
    st.dataframe(
        df_stock[['Ingrediente', 'Stock_Actual', 'Unidad_Base', 'Costo_Ponderado']], 
        hide_index=True,
        use_container_width=True
    )

# --- MODULO PRODUCIDO ---
with tab_producido:
    st.header("📦 Stock Producido")
    df_prod = get_df("lotes_produccion")
    if not df_prod.empty:
        # Resumen visual
        resumen_p = df_prod.groupby("Producto")["Cantidad_Envases"].sum().reset_index()
        st.dataframe(resumen_p, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📥 Exportar para Impresora Inkjet")
        st.caption("Genera un CSV con Lote, Elaboración y Vencimiento (12 meses).")
        
        from modules.data_manager import prepare_inkjet_export
        txt_content = prepare_inkjet_export(df_prod)
        
        if txt_content:
            st.download_button(
                label="⬇️ Descargar TXT para ASJet",
                data=txt_content,
                file_name=f"lotes_asjet_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                help="Copiá este archivo .txt al pendrive para la impresora Asjet."
            )
            
            with st.expander("Ver vista previa del texto"):
                st.code(txt_content)
    else:
        st.info("Sin registros de producción.")

# --- MODULO VENTAS ---
with tab_ventas:
    st.header("📈 Historial de Ventas")
    df_v = get_df("ventas")
    if not df_v.empty:
        st.dataframe(
            df_v[['Fecha_Venta', 'Cliente', 'Cantidad_Vendida_KG', 'Precio_Total']].sort_values("Fecha_Venta", ascending=False),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Sin ventas registradas.")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Rojo Malbec Engineering | Lab App v1.1")
