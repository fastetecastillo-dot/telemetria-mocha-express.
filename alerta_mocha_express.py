
import os
import requests
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE SUPABASE
# ==========================================
SUPABASE_URL = "https://sqnjzxaghorbqobgmph.supabase.co"
SUPABASE_KEY = "sb_publishable_HCBX9iS60_IbcSMSP6Pgvg_jmh9Skgv"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def evaluar_y_actualizar_clima():
    print("Iniciando evaluación meteorológica automatizada para Lancha Mocha Express...")
    
    # Límites operativos configurados:
    # Viento máximo (Vmax) <= 16 nudos
    # Altura de ola máxima (Hmax) <= 2.2 metros
    
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    
    # Aquí puedes conectar tu lógica de pronóstico (ej. Windguru / API meteorológica)
    # Definimos el estado y la ventana horaria resultante:
    estado_calculado = "OPERATIVO"  # Cambiará a "SUSPENDIDO" si supera los límites
    ventana = "08:00 - 18:00 hrs"
    
    try:
        # Inserta o actualiza el registro del día en la tabla 'dias_operativos' de Supabase
        data, count = supabase.table("dias_operativos").upsert({
            "fecha": fecha_hoy,
            "estado": estado_calculado,
            "ventana_horaria": ventana
        }, on_conflict=["fecha"]).execute()
        
        print(f"Supabase actualizado con éxito para el día {fecha_hoy}: Estado -> {estado_calculado}")
        
    except Exception as e:
        print(f"Error al conectar o actualizar la base de datos: {e}")

if __name__ == "__main__":
    evaluar_y_actualizar_clima()
