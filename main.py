from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from pydantic import BaseModel, validator
from pydantic import root_validator 
from dotenv import load_dotenv
from typing import Optional
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
                consecutivo, fecha_formulario, latitud, longitud,
                nombre_solicitante, al_sur, al_norte, al_occidente, al_oriente,
                sector, edificio, lote, tipologia, topografia, construccion,
                sotanos, zonas_comunes, piso, vista,
                formato_url, plano_url, id_usuario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            data.consecutivo, data.fecha_formulario, data.latitud, data.longitud,
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

class VisitaForm(BaseModel):
    consecutivo: str
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
def mostrar_formulario(request: Request, exito: int = 0):
    usuarios = obtener_usuarios()
    return templates.TemplateResponse("form.html", {"request": request, "usuarios": usuarios, "exito": exito})

@app.post("/enviar")
async def recibir_formulario(request: Request,
    consecutivo: str = Form(...),
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
        consecutivo=consecutivo,
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
    return RedirectResponse("/?exito=1", status_code=303)

@app.get("/enviar", include_in_schema=False)
def redirigir_si_get():
    return RedirectResponse("/", status_code=303)

@app.get("/mapa", response_class=HTMLResponse)
def mostrar_mapa(request: Request):
    return templates.TemplateResponse("mapa.html", {"request": request})

@app.get("/api/avaluos")
def api_avaluos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_avaluo, consecutivo, direccion, ST_X(geom), ST_Y(geom)
        FROM app.avaluo
        WHERE geom IS NOT NULL
    """)
    data = [
        {
            "id_avaluo": row[0],
            "consecutivo": row[1],
            "direccion": row[2],
            "lon": row[3],
            "lat": row[4],
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return JSONResponse(data)

