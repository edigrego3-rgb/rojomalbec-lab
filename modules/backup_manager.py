
# modules/backup_manager.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from modules.data_manager import FILES, get_connection, SHEET_NAME

# Path relativo para backups (funciona desde cualquier ubicación)
BACKUP_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backup")

def respaldo_local():
    """Descarga todas las tablas de session_state y las guarda en /backup/ con fecha."""
    try:
        # 1. Crear directorio con fecha
        folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        target_dir = os.path.join(BACKUP_BASE_DIR, folder_name)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        # 2. Guardar cada tabla
        for key in FILES.keys():
            if key in st.session_state:
                df = st.session_state[key]
                file_path = os.path.join(target_dir, f"{key}.csv")
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return True, target_dir
    except Exception as e:
        return False, str(e)

def respaldo_drive():
    """Crea una copia del Spreadsheet 'RojoMalbec DB' en Google Drive."""
    gc = get_connection()
    if not gc:
        return False, "No hay conexión con Google Sheets."
        
    try:
        # Abrir el archivo original
        sh = gc.open(SHEET_NAME)
        
        # Nombre de la copia
        new_name = f"{SHEET_NAME}_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
        
        # Crear copia
        # Nota: gc.copy() es el método para copiar un spreadsheet
        gc.copy(sh.id, title=new_name)
        
        return True, new_name
    except Exception as e:
        return False, str(e)
