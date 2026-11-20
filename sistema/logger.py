"""Configura el registro de eventos y errores del sistema.

Escribe todo lo relevante en `logs/eventos.log`. Si por algún motivo no se
puede abrir o crear el archivo, el programa continúa sin problemas y deja
los avisos en consola.
"""
import logging
from pathlib import Path

CARPETA_LOGS = Path(__file__).resolve().parent.parent / "logs"
ARCHIVO_LOG = CARPETA_LOGS / "eventos.log"
NOMBRE_LOGGER = "software_fj"


def configurar_logger() -> logging.Logger:
    """Obtiene o inicializa el logger una sola vez para no duplicar salidas."""
    logger = logging.getLogger(NOMBRE_LOGGER)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # En consola solo mostramos avisos y errores para no llenar la pantalla
    manejador_consola = logging.StreamHandler()
    manejador_consola.setLevel(logging.WARNING)
    manejador_consola.setFormatter(formato)
    logger.addHandler(manejador_consola)

    # En archivo guardamos todo el detalle desde DEBUG
    try:
        CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
        manejador_archivo = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
        manejador_archivo.setLevel(logging.DEBUG)
        manejador_archivo.setFormatter(formato)
        logger.addHandler(manejador_archivo)
    except OSError as error:
        logger.warning(
            "No pudimos abrir el archivo de log (%s); seguimos solo por consola.",
            error,
        )

    return logger