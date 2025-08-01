from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from pydantic import BaseModel, validator
from pydantic import root_validator 
from dotenv import load_dotenv
from typing import Optional
import json
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def obtener_usuarios():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id_usuario, nombre FROM app.usuario ORDER BY nombre;")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return usuarios

def insertar_visita(data):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO app.visita (
                id_asignacion, fecha_formulario, latitud, longitud,
                nombre_solicitante, al_sur, al_norte, al_occidente, al_oriente,
                sector, edificio, lote, tipologia, topografia, construccion,
                sotanos, zonas_comunes, piso, vista,
                formato_url, plano_url, id_usuario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            data.id_asignacion, data.fecha_formulario, data.latitud, data.longitud,
            data.nombre_solicitante, data.al_sur, data.al_norte, data.al_occidente, data.al_oriente,
            data.sector, data.edificio, data.lote, data.tipologia, data.topografia, data.construccion,
            data.sotanos, data.zonas_comunes, data.piso, data.vista,
            data.formato_url, data.plano_url, data.id_usuario
        ))
        conn.commit()
        cur.close()
        conn.close()
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Consecutivo duplicado u otro error de integridad.")
    except Exception as e:
        print("⚠️ ERROR al insertar la visita:", e)  # Esto lo verás en la consola del servidor
        raise HTTPException(status_code=500, detail=f"Error al insertar la visita: {e}")

def obtener_municipios():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, mpio_cnmbr FROM app.municipio ORDER BY mpio_cnmbr;")
    municipios = cur.fetchall()
    cur.close()
    conn.close()
    return municipios

def obtener_consecutivos_pendientes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id, a.consecutivo, a.fecha_asignacion
        FROM app.asignacion a
        LEFT JOIN app.visita v ON a.id = v.id_asignacion
        WHERE v.id_asignacion IS NULL
            AND a.fecha_asignacion IS NOT NULL
            AND a.fecha_visita IS NOT NULL
            AND a.hora_visita IS NOT NULL
            AND (a.fecha_visita + a.hora_visita)::timestamp <= NOW()
            AND a.fecha_entrega IS NULL
            AND a.solo_fotos IS FALSE
        ORDER BY a.fecha_visita ASC, a.hora_visita ASC
    """)
    consecutivos = cur.fetchall()
    cur.close()
    conn.close()
    return consecutivos

class VisitaForm(BaseModel):
    id_asignacion: int
    fecha_formulario: str
    coordenadas: str
    latitud: float
    longitud: float

    nombre_solicitante: Optional[str] = None
    al_sur: Optional[str] = None
    al_norte: Optional[str] = None
    al_occidente: Optional[str] = None
    al_oriente: Optional[str] = None
    sector: Optional[str] = None
    edificio: Optional[str] = None
    lote: Optional[str] = None
    tipologia: Optional[str] = None
    topografia: Optional[str] = None
    construccion: Optional[str] = None
    sotanos: Optional[str] = None
    zonas_comunes: Optional[str] = None
    piso: Optional[str] = None
    vista: Optional[str] = None
    formato_url: Optional[str] = None
    plano_url: Optional[str] = None
    id_usuario: Optional[int] = None

    @root_validator(pre=True)
    def separar_latitud_y_longitud(cls, values):
        coords = values.get("coordenadas")
        if coords:
            partes = coords.split(",")
            if len(partes) != 2:
                raise ValueError("Formato inválido, usar: lat, lon")
            try:
                lat = float(partes[0].strip())
                lon = float(partes[1].strip())
            except ValueError:
                raise ValueError("Las coordenadas deben ser números")
            values["latitud"] = lat
            values["longitud"] = lon
        return values

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/form_visita", response_class=HTMLResponse)
def mostrar_formulario(request: Request, exito: int = 0):
    usuarios = obtener_usuarios()
    consecutivos = obtener_consecutivos_pendientes()
    return templates.TemplateResponse("form.html", {
        "request": request, 
        "usuarios": usuarios, 
        "consecutivos": consecutivos,
        "exito": exito
    })

@app.post("/enviar")
async def recibir_formulario(request: Request,
    id_asignacion: int = Form(...),
    fecha_formulario: str = Form(...),
    coordenadas: str = Form(...),
    nombre_solicitante: Optional[str] = Form(None),
    al_sur: Optional[str] = Form(None),
    al_norte: Optional[str] = Form(None),
    al_occidente: Optional[str] = Form(None),
    al_oriente: Optional[str] = Form(None),
    sector: Optional[str] = Form(None),
    edificio: Optional[str] = Form(None),
    lote: Optional[str] = Form(None),
    tipologia: Optional[str] = Form(None),
    topografia: Optional[str] = Form(None),
    construccion: Optional[str] = Form(None),
    sotanos: Optional[str] = Form(None),
    zonas_comunes: Optional[str] = Form(None),
    piso: Optional[str] = Form(None),
    vista: Optional[str] = Form(None),
    formato_url: Optional[str] = Form(None),
    plano_url: Optional[str] = Form(None),
    id_usuario: int = Form(None),
):
    form = VisitaForm(
        id_asignacion=id_asignacion,
        fecha_formulario=fecha_formulario,
        coordenadas=coordenadas,
        nombre_solicitante=nombre_solicitante,
        al_sur=al_sur,
        al_norte=al_norte,
        al_occidente=al_occidente,
        al_oriente=al_oriente,
        sector=sector,
        edificio=edificio,
        lote=lote,
        tipologia=tipologia,
        topografia=topografia,
        construccion=construccion,
        sotanos=sotanos,
        zonas_comunes=zonas_comunes,
        piso=piso,
        vista=vista,
        formato_url=formato_url,
        plano_url=plano_url,
        id_usuario=id_usuario,
    )
    insertar_visita(form)
    return RedirectResponse("/form_visita?exito=1", status_code=303)

@app.get("/enviar", include_in_schema=False)
def redirigir_si_get():
    return RedirectResponse("/form_visita", status_code=303)

@app.get("/geovisor", response_class=HTMLResponse)
def mostrar_mapa(request: Request):
    return templates.TemplateResponse("mapa.html", {"request": request})

CAPAS = {
    "mov_masa": {
        "tabla": "app.am_mov_masa",
        "tipo": "polygon",
        "nombre": "Movimientos de Masa",
        "sql": """
            SELECT 
                CASE 
                    WHEN categoriza = 1 THEN 'Baja'
                    WHEN categoriza = 2 THEN 'Media'
                    WHEN categoriza = 3 THEN 'Alta'
                    ELSE 'Sin clasificar'
                END as categorizacion,
                area_zonif, 
                clase_suel, 
                ST_AsGeoJSON(geom)::json as geom 
            FROM app.am_mov_masa 
            WHERE geom IS NOT NULL
        """
    },
    "area_actividad": {
        "tabla": "app.area_actividad",
        "tipo": "polygon",
        "nombre": "Áreas de Actividad",
        "sql": "SELECT codigo_area_actividad as codigo, nombre_area_actividad as tipo, ST_AsGeoJSON(geom)::json as geom FROM app.area_actividad WHERE geom IS NOT NULL"
    },
    "avaluo": {
        "tabla": "app.avaluo",
        "tipo": "point",
        "nombre": "Avalúos",
        "sql": """
            SELECT 
                consecutivo, 
                area_privada, 
                TO_CHAR(valor_m2, '$999G999G999') as valor_m2, 
                direccion, 
                vetustez,
                ST_AsGeoJSON(geom)::json as geom 
            FROM app.avaluo 
            WHERE geom IS NOT NULL
        """
    },
    "barrios": {
        "tabla": "app.barrios",
        "tipo": "polygon",
        "nombre": "Barrios",
        "sql": "SELECT scanombre as nombre, ST_AsGeoJSON(geom)::json as geom FROM app.barrios WHERE geom IS NOT NULL"
    },
    "localidades": {
        "tabla": "app.localidades",
        "tipo": "polygon",
        "nombre": "Localidades",
        "sql": "SELECT locnombre as localidad, ST_AsGeoJSON(geom)::json as geom FROM app.localidades WHERE geom IS NOT NULL"
    },
    "mz_estr": {
        "tabla": "app.mz_estr",
        "tipo": "polygon",
        "nombre": "Estratificación",
        "sql": "SELECT estrato, ST_AsGeoJSON(geom)::json as geom FROM app.mz_estr WHERE geom IS NOT NULL"
    },
    "oferta": {
        "tabla": "app.oferta",
        "tipo": "point",
        "nombre": "Ofertas",
        "sql": """
            SELECT id_oferta as id, precio, area_privada, ST_AsGeoJSON(geom)::json as geom 
            FROM app.oferta 
            WHERE geom IS NOT NULL
        """
    },
    "sitios_de_interes": {
        "tabla": "app.sitios_de_interes",
        "tipo": "point",
        "nombre": "Sitios de Interés",
        "sql": "SELECT ngenombre, ngeclasifi, ST_AsGeoJSON(geom)::json as geom FROM app.sitios_de_interes WHERE geom IS NOT NULL"
    },
    "tratamientos": {
        "tabla": "app.tratamientos",
        "tipo": "polygon",
        "nombre": "Tratamientos Urbanísticos",
        "sql": "SELECT nombre_tratamiento, tipologia, altura_maxima, ST_AsGeoJSON(geom)::json as geom FROM app.tratamientos WHERE geom IS NOT NULL"
    }
}

@app.get("/api/capa/{nombre_capa}")
def api_capa(nombre_capa: str):
    capa = CAPAS.get(nombre_capa)
    if not capa:
        return JSONResponse({"error": "Capa no encontrada"}, status_code=404)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(capa["sql"])
    features = []
    for row in cur.fetchall():
        columns = [desc[0] for desc in cur.description]
        props = {k: v for k, v in zip(columns, row) if k != "geom"}
        features.append({
            "type": "Feature",
            "geometry": row[columns.index("geom")],
            "properties": props
        })
    geojson = {"type": "FeatureCollection", "features": features}
    cur.close()
    conn.close()
    return JSONResponse(geojson)

@app.get("/api/lista_capas")
def lista_capas():
    # Devuelve la lista y nombres personalizados
    return [{"id": k, "nombre": v["nombre"], "tipo": v["tipo"]} for k,v in CAPAS.items()]

@app.get("/form_asignacion", response_class=HTMLResponse)
def mostrar_form_asignacion(request: Request, exito: int = 0):
    municipios = obtener_municipios()
    return templates.TemplateResponse(
        "form_asignacion.html",
        {"request": request, "municipios": municipios, "exito": exito}
    )

@app.post("/enviar_asignacion")
async def recibir_form_asignacion(
    consecutivo: str = Form(...),
    fecha_asignacion: str = Form(...),
    municipio_id: int = Form(...),
    solo_fotos: Optional[str] = Form(None),  # Recibe "true" si está marcado
):
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Choices.js y HTML envían solo_fotos="true" si está marcado, None si no
        cur.execute("""
            INSERT INTO app.asignacion (consecutivo, fecha_asignacion, municipio_id, solo_fotos)
            VALUES (%s, %s, %s, %s);
        """, (
            consecutivo,
            fecha_asignacion,
            municipio_id,
            solo_fotos == "true"
        ))
        conn.commit()
        cur.close()
        conn.close()
        return RedirectResponse("/form_asignacion?exito=1", status_code=303)
    except Exception as e:
        print("Error al insertar asignacion:", e)
        raise HTTPException(status_code=500, detail="Error al guardar la asignación.")

@app.get("/dashboard", response_class=HTMLResponse)
def ver_dashboard(request: Request):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.*, m.mpio_cnmbr AS municipio
        FROM app.asignacion a
        LEFT JOIN app.municipio m ON a.municipio_id = m.id
        ORDER BY fecha_asignacion DESC;
    """)
    asignaciones = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "asignaciones": asignaciones
    })

@app.post("/update-asignacion")
async def update_asignacion(request: Request):
    data = await request.json()
    consecutivo = data.get("consecutivo")
    campo = data.get("campo")
    valor = data.get("valor")

    if campo not in ["fecha_visita", "hora_visita", "fecha_entrega", "observaciones"]:
        return JSONResponse(content={"error": "Campo inválido"}, status_code=400)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE app.asignacion
            SET {campo} = %s
            WHERE consecutivo = %s
        """, (valor if valor != "" else None, consecutivo))
        conn.commit()
        cur.close()
        conn.close()
        return {"mensaje": "ok"}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
