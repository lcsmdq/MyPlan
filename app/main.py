from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from app.routers import favorites
from app.database import Base
from app.routers import events,  assists, auth  # 👈Importa los routerpip freeze 


#Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Eventos API",
    description="API para gestión de eventos",
    version="1.0.0"
)
# 👇 Configuración global de seguridad para Swagger UI
security = HTTPBearer()

# 👇 Muy importante: registrar el router ANTES de cualquier endpoint que pueda solaparse
app.include_router(events.router)
app.include_router(assists.router)
app.include_router(auth.router)
app.include_router(favorites.router)

# Endpoint Ruta raíz
@app.get("/")
def root():
    return {"message": "¡API funcionando correctamente!"}


