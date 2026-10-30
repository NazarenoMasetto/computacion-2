"""Modelos de datos: estados, tipos de tarea y la tarea en sí."""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Estado(str, Enum):
    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


# Estados de los que una tarea ya no sale.
FINALES = {Estado.COMPLETADA, Estado.FALLIDA, Estado.CANCELADA}


class TipoTarea(str, Enum):
    DESCARGAR = "descargar"
    HASHEAR = "hashear"
    ESPERAR = "esperar"


class TareaIn(BaseModel):
    """Lo que manda el cliente en el POST."""
    tipo: TipoTarea
    parametros: dict[str, Any] = {}
    timeout: float | None = Field(default=None, gt=0)


class Tarea(BaseModel):
    """Una tarea tal como la guarda y la devuelve el sistema."""
    id: str
    tipo: TipoTarea
    parametros: dict[str, Any]
    timeout: float
    estado: Estado = Estado.PENDIENTE
    resultado: Any = None
    error: str | None = None
    creada: float
    iniciada: float | None = None
    finalizada: float | None = None
