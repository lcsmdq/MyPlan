from fastapi import FastAPI
from .database import Base, engine
from .routers import events  # 👈 Importa el router

#Base.metadata.create_all(bind=engine)

app = FastAPI(title="Eventos API")

# 👇 Muy importante: registrar el router ANTES de cualquier endpoint que pueda solaparse
app.include_router(events.router)

# Endpoint Ruta raíz
@app.get("/")
def root():
    return {"message": "¡API funcionando correctamente!"}

