"""Conexión a Neo4j AuraDB.

Las credenciales se leen exclusivamente de variables de entorno (archivo .env local),
nunca se escriben en el código.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, RoutingControl

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


class ConfiguracionError(RuntimeError):
    pass


def _desde_secrets() -> None:
    """En Streamlit Community Cloud las credenciales llegan como Secrets: se copian al entorno."""
    try:
        import streamlit as st
        for clave in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "NEO4J_DATABASE"):
            if not os.getenv(clave) and clave in st.secrets:
                os.environ[clave] = str(st.secrets[clave])
    except Exception:  # noqa: BLE001  (sin secrets.toml o fuera de Streamlit)
        pass


def _config() -> dict[str, str]:
    _desde_secrets()
    faltan = [v for v in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD") if not os.getenv(v)]
    if faltan:
        raise ConfiguracionError(
            "Faltan variables en .env: " + ", ".join(faltan) + ". Copie .env.example como .env y complételo."
        )
    return {
        "uri": os.environ["NEO4J_URI"],
        "user": os.environ["NEO4J_USERNAME"],
        "password": os.environ["NEO4J_PASSWORD"],
        "database": os.getenv("NEO4J_DATABASE") or "neo4j",
    }


@lru_cache(maxsize=1)
def get_driver() -> Driver:
    cfg = _config()
    # Las notificaciones informativas del servidor (p. ej. "propiedad aún no existe") se silencian;
    # los errores reales siguen lanzándose como excepciones.
    driver = GraphDatabase.driver(cfg["uri"], auth=(cfg["user"], cfg["password"]),
                                  notifications_min_severity="OFF")
    driver.verify_connectivity()
    return driver


def database() -> str:
    return _config()["database"]


def leer(query: str, **params: Any) -> list[dict]:
    """Ejecuta una consulta de solo lectura con parámetros y devuelve una lista de diccionarios."""
    records, _, _ = get_driver().execute_query(
        query, parameters_=params, database_=database(), routing_=RoutingControl.READ
    )
    return [r.data() for r in records]


def escribir(query: str, **params: Any) -> list[dict]:
    """Ejecuta una consulta de escritura con parámetros (transacción gestionada)."""
    records, _, _ = get_driver().execute_query(
        query, parameters_=params, database_=database(), routing_=RoutingControl.WRITE
    )
    return [r.data() for r in records]


def leer_registros(query: str, **params: Any):
    """Devuelve los Record originales (necesario para rutas/objetos Path)."""
    records, _, _ = get_driver().execute_query(
        query, parameters_=params, database_=database(), routing_=RoutingControl.READ
    )
    return records


def cerrar() -> None:
    if get_driver.cache_info().currsize:
        get_driver().close()
        get_driver.cache_clear()
