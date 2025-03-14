from fastapi import FastAPI, HTTPException, Header, Query, Depends
import requests

app = FastAPI()

# 🔹 URL base de la API de Dragonfish
DRAGONFISH_API_URL = "http://vpn.microsite.com.ar:8009/api.Dragonfish"

# 🔹 Clave interna de autenticación para nuestra API intermedia
CLAVE_INTERNA = "AMIORE2025"

# 🔹 Token de Dragonfish (Oculto para los usuarios de la API intermedia)
TOKEN_DRAGONFISH = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3OTM5MDQ3MzksInVzdWFyaW8iOiJBRE1JTiIsInBhc3N3b3JkIjoiNGE3ZDkxOGJjNzFhZWY0NzViMTZmNjgxZDRkMmVhM2Y3YTc5ZTAxYjM3NjRlNTExZTA2MDExZmQ5ZjhmOGZkOSJ9.WdeEF1st0yCgCGlH9g_77iJ4EtbM9OFX5QxcWG1jKew"

# 🔹 Función para validar autenticación en nuestra API intermedia
def verificar_autenticacion(api_key: str = Header(..., description="Clave de autenticación de nuestra API")):
    if api_key != CLAVE_INTERNA:
        raise HTTPException(status_code=401, detail="Clave de autenticación inválida.")

# 🔹 Función auxiliar para hacer solicitudes a Dragonfish con autenticación oculta
def consultar_api_dragonfish(endpoint: str, id_cliente: str, limit: int, page: int):
    headers = {
        "accept": "application/json",
        "IdCliente": id_cliente,
        "Authorization": TOKEN_DRAGONFISH  # Token oculto
    }

    url = f"{DRAGONFISH_API_URL}/{endpoint}/?limit={limit}&page={page}"
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="No autorizado en Dragonfish.")
    elif response.status_code == 403:
        raise HTTPException(status_code=403, detail="Acceso prohibido en Dragonfish.")
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="No encontrado.")
    elif response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error en la API de Dragonfish.")

    return response.json()

# 🔹 Funciones de filtrado para cada módulo
def filtrar_comprobantes_caja(data):
    return {"Resultados": [
        {
            "CajaOrigen": item.get("CajaOrigen"),
            "CajaDestino": item.get("CajaDestino"),
            "Concepto": item.get("Concepto"),
            "Fecha": item.get("Fecha"),
            "Identificador": item.get("Identificador"),
            "Numero": item.get("Numero"),
            "Observacion": item.get("Observacion"),
            "OrigenDestino": item.get("OrigenDestino"),
            "Tipo": item.get("Tipo"),
            "Valores": [{"Monto": v.get("Monto"), "ValorDetalle": v.get("ValorDetalle")} for v in item.get("Valores", [])]
        }
        for item in data.get("Resultados", [])
    ]}

def filtrar_remitos_venta(data):
    return {"Resultados": [
        {
            "Cliente": item.get("Cliente"),
            "ClienteDescripcion": item.get("ClienteDescripcion"),
            "Codigo": item.get("Codigo"),
            "CompAfec": [{"TipoCompCaracter": c.get("TipoCompCaracter"), "Total": c.get("Total")} for c in item.get("CompAfec", [])],
            "FacturaDetalle": [{
                "Articulo": f.get("Articulo"),
                "ArticuloDetalle": f.get("ArticuloDetalle"),
                "Cantidad": f.get("Cantidad"),
                "Precio": f.get("Precio")
            } for f in item.get("FacturaDetalle", [])],
            "Fecha": item.get("Fecha"),
            "Total": item.get("Total")
        }
        for item in data.get("Resultados", [])
    ]}

def filtrar_recibos(data):
    return {"Resultados": [
        {
            "Cliente": item.get("Cliente"),
            "ClienteDescripcion": item.get("ClienteDescripcion"),
            "Codigo": item.get("Codigo"),
            "Fecha": item.get("Fecha"),
            "Numero": item.get("Numero"),
            "Total": item.get("Total"),
            "ReciboDetalle": [{
                "Descripcion": r.get("Descripcion"),
                "Fecha": r.get("Fecha"),
                "Monto": r.get("Monto")
            } for r in item.get("ReciboDetalle", [])]
        }
        for item in data.get("Resultados", [])
    ]}

# **Endpoints para cada módulo**
@app.get("/articulos", dependencies=[Depends(verificar_autenticacion)])
def obtener_articulos(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return consultar_api_dragonfish("Articulo", id_cliente, limit, page)

@app.get("/clientes", dependencies=[Depends(verificar_autenticacion)])
def obtener_clientes(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return consultar_api_dragonfish("Cliente", id_cliente, limit, page)

@app.get("/comprobantes_caja", dependencies=[Depends(verificar_autenticacion)])
def obtener_comprobantes_caja(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return filtrar_comprobantes_caja(consultar_api_dragonfish("Comprobantedecaja", id_cliente, limit, page))

@app.get("/remitos_venta", dependencies=[Depends(verificar_autenticacion)])
def obtener_remitos_venta(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return filtrar_remitos_venta(consultar_api_dragonfish("Remito", id_cliente, limit, page))

@app.get("/recibos", dependencies=[Depends(verificar_autenticacion)])
def obtener_recibos(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return filtrar_recibos(consultar_api_dragonfish("Recibo", id_cliente, limit, page))

@app.get("/cancelacion_venta", dependencies=[Depends(verificar_autenticacion)])
def obtener_cancelaciones_venta(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return consultar_api_dragonfish("Devolucion", id_cliente, limit, page)

@app.get("/facturas_venta", dependencies=[Depends(verificar_autenticacion)])
def obtener_facturas_venta(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return consultar_api_dragonfish("Factura", id_cliente, limit, page)

# **Endpoint para obtener todos los módulos juntos**
@app.get("/datos_completos", dependencies=[Depends(verificar_autenticacion)])
def obtener_datos_completos(id_cliente: str = Header(...), limit: int = 50, page: int = 1):
    return {
        "articulos": consultar_api_dragonfish("Articulo", id_cliente, limit, page),
        "clientes": consultar_api_dragonfish("Cliente", id_cliente, limit, page),
        "comprobantes_caja": filtrar_comprobantes_caja(consultar_api_dragonfish("Comprobantedecaja", id_cliente, limit, page)),
        "remitos_venta": filtrar_remitos_venta(consultar_api_dragonfish("Remito", id_cliente, limit, page)),
        "recibos": filtrar_recibos(consultar_api_dragonfish("Recibo", id_cliente, limit, page)),
        "cancelaciones_venta": consultar_api_dragonfish("Devolucion", id_cliente, limit, page),
        "facturas_venta": consultar_api_dragonfish("Factura", id_cliente, limit, page)
    }
