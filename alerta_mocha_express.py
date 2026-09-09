
import requests
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN DE CORREO SMTP
# ==========================================
CORREO_REMITENTE = 'f.astetecastillo@gmail.com'
CLAVE_APLICACION = os.environ.get('CLAVE_APP_GMAIL')
CORREOS_DESTINO = ['f.astetecastillo@gmail.com', 'luisastetecastillo@gmail.com', 'guanajascuba@gmail.com']

# ==========================================
# 2. PARÁMETROS TÉCNICOS OPERATIVOS
# ==========================================
COORD_TIRUA = {"lat": -38.33, "lon": -73.49}
COORD_MOCHA = {"lat": -38.37, "lon": -73.91}
LIMITE_OLA_M = 2.2
LIMITE_VIENTO_KN = 16.0

def enviar_correo(asunto, cuerpo_texto):
    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        if not CLAVE_APLICACION:
            raise ValueError("No se encontró la variable CLAVE_APP_GMAIL en el servidor.")
        servidor.login(CORREO_REMITENTE, str(CLAVE_APLICACION).replace(" ", ""))
        mensaje = MIMEMultipart()
        mensaje['From'] = f"Mocha Express Sys <{CORREO_REMITENTE}>"
        mensaje['To'] = ", ".join(CORREOS_DESTINO)
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(cuerpo_texto, 'plain', 'utf-8'))
        servidor.sendmail(CORREO_REMITENTE, CORREOS_DESTINO, mensaje.as_string())
        servidor.quit()
    except Exception as e:
        print(f"Error de envío: {e}")

def obtener_datos():
    hoy = datetime.now()
    fecha_fin = hoy + timedelta(days=12)
    f_inicio_str = hoy.strftime('%Y-%m-%d')
    f_fin_str = fecha_fin.strftime('%Y-%m-%d')

    urls = {
        'mar_tirua': f"https://marine-api.open-meteo.com/v1/marine?latitude={COORD_TIRUA['lat']}&longitude={COORD_TIRUA['lon']}&hourly=wave_height,wave_period,sea_level_height_msl&timezone=America%2FSantiago&start_date={f_inicio_str}&end_date={f_fin_str}",
        'mar_mocha': f"https://marine-api.open-meteo.com/v1/marine?latitude={COORD_MOCHA['lat']}&longitude={COORD_MOCHA['lon']}&hourly=wave_height,wave_period,sea_level_height_msl&timezone=America%2FSantiago&start_date={f_inicio_str}&end_date={f_fin_str}",
        'viento_tirua': f"https://api.open-meteo.com/v1/forecast?latitude={COORD_TIRUA['lat']}&longitude={COORD_TIRUA['lon']}&hourly=windspeed_10m,windgusts_10m&windspeed_unit=kn&timezone=America%2FSantiago&start_date={f_inicio_str}&end_date={f_fin_str}",
        'viento_mocha': f"https://api.open-meteo.com/v1/forecast?latitude={COORD_MOCHA['lat']}&longitude={COORD_MOCHA['lon']}&hourly=windspeed_10m,windgusts_10m&windspeed_unit=kn&timezone=America%2FSantiago&start_date={f_inicio_str}&end_date={f_fin_str}"
    }

    try:
        datos = {k: requests.get(v).json()['hourly'] for k, v in urls.items()}
        tiempos = datos['mar_tirua']['time']

        total_horas = len(tiempos)
        horas_viables = 0
        horas_luz_procesadas = 0
        datos_por_dia = {}

        for i in range(total_horas):
            hora_actual = datetime.fromisoformat(tiempos[i])
            fecha_str = hora_actual.strftime('%d-%m-%Y')

            if fecha_str not in datos_por_dia:
                datos_por_dia[fecha_str] = {'ventanas': [], 'mareas': []}

            try:
                nivel = datos['mar_mocha']['sea_level_height_msl'][i]
                if nivel is not None:
                    datos_por_dia[fecha_str]['mareas'].append((hora_actual, nivel))
            except:
                pass

            if 7 <= hora_actual.hour <= 19:
                o_tirua = datos['mar_tirua']['wave_height'][i]
                o_mocha = datos['mar_mocha']['wave_height'][i]
                v_tirua = datos['viento_tirua']['windspeed_10m'][i]
                v_mocha = datos['viento_mocha']['windspeed_10m'][i]
                p_tirua = datos['mar_tirua']['wave_period'][i]
                p_mocha = datos['mar_mocha']['wave_period'][i]
                r_tirua = datos['viento_tirua']['windgusts_10m'][i]
                r_mocha = datos['viento_mocha']['windgusts_10m'][i]

                if None in (o_tirua, o_mocha, v_tirua, v_mocha, p_tirua, p_mocha, r_tirua, r_mocha):
                    continue
                
                horas_luz_procesadas += 1

                if (o_tirua <= LIMITE_OLA_M and o_mocha <= LIMITE_OLA_M and
                    v_tirua <= LIMITE_VIENTO_KN and v_mocha <= LIMITE_VIENTO_KN):

                    horas_viables += 1
                    datos_por_dia[fecha_str]['ventanas'].append({
                        'hora': hora_actual.strftime('%H:%M'),
                        'o_max': max(o_tirua, o_mocha),
                        'v_max': max(v_tirua, v_mocha),
                        'r_max': max(r_tirua, r_mocha), 
                        'p_max': max(p_tirua, p_mocha)
                    })

        tasa_viabilidad = round((horas_viables / horas_luz_procesadas) * 100, 1) if horas_luz_procesadas > 0 else 0

        reporte = f"REPORTE TÉCNICO DE OPERACIONES - MOCHA EXPRESS\n"
        reporte += f"Periodo de Proyección: {f_inicio_str} al {f_fin_str} (12 días)\n"
        reporte += f"Tasa de Viabilidad Operativa: {tasa_viabilidad}% de las horas diurnas evaluadas.\n"
        reporte += f"Parámetros Estrictos: Ola máx {LIMITE_OLA_M}m | Viento sostenido máx {LIMITE_VIENTO_KN}kn.\n"
        reporte += "-" * 70 + "\n\n"

        hay_ventanas = any(len(info['ventanas']) > 0 for info in datos_por_dia.values())

        if not hay_ventanas:
            reporte += "ALERTA ROJA: 0% de viabilidad. No se detectan ventanas operativas seguras en el periodo evaluado.\n\n"

        reporte += "DETALLE DIARIO (Mareas y Ventanas de Zarpe):\n\n"

        for dia, info in datos_por_dia.items():
            horas_ventana = info['ventanas']
            mareas = info['mareas']

            texto_marea = ""
            if mareas:
                mareas_ordenadas = sorted(mareas, key=lambda x: x[1])
                bajamar = mareas_ordenadas[0]
                pleamar = mareas_ordenadas[-1]
                texto_marea = f"🌊 Pleamar (Alta): {pleamar[0].strftime('%H:%M')} hrs | Bajamar (Baja): {bajamar[0].strftime('%H:%M')} hrs"

            reporte += f"► Fecha: {dia}\n"
            reporte += f"   - {texto_marea}\n"

            if horas_ventana:
                inicio = horas_ventana[0]['hora']
                fin = horas_ventana[-1]['hora']
                o_peak = max([h['o_max'] for h in horas_ventana])
                v_peak = max([h['v_max'] for h in horas_ventana])
                r_peak = max([h['r_max'] for h in horas_ventana])
                p_peak = max([h['p_max'] for h in horas_ventana])
                
                reporte += f"   - ✅ Ventana Útil Autorizada: {inicio} a {fin} hrs.\n"
                reporte += f"   - Peak Ola: {o_peak}m | Viento Sost: {v_peak}kn | Rachas: {r_peak}kn | Periodo Máx: {p_peak}s.\n\n"
            else:
                reporte += f"   - ❌ Sin ventanas operativas seguras este día.\n\n"

        reporte += "-" * 70 + "\n"
        reporte += "NOTA DE MAREAS: Las estimaciones son generadas por modelos de interpolación global. Para contrastación regulatoria final, cotejar con las tablas de mareas oficiales (SHOA)."

        estado_global = "VENTANAS DETECTADAS" if hay_ventanas else "RUTAS CERRADAS"
        asunto = f"[{estado_global}] Proyección Operativa Mocha Express 12 Días - {tasa_viabilidad}% Viabilidad"

        enviar_correo(asunto, reporte)
        print("Ejecución automatizada finalizada. Reporte técnico enviado.")

    except Exception as e:
        print(f"Error procesando datos: {e}")

if __name__ == '__main__':
    obtener_datos()
