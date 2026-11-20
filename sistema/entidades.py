"""Base común para las entidades del sistema Software FJ."""
import itertools
from abc import ABC, abstractmethod

from .excepciones import ParametroFaltanteError


def exigir(valor, campo):
    """Valida que un campo no venga vacío ni sea None; si pasa, devuelve el valor."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ParametroFaltanteError(f"Falta completar el campo '{campo}'.")
    return valor


class EntidadBase(ABC):
    """Clase base para entidades que necesitan un ID correlativo (ej. CLI-0001)."""

    _prefijo = "ENT"
    _secuencia = itertools.count(1)

    def __init__(self):
        # Compartimos el contador entre instancias para que los IDs no se repitan
        numero = next(EntidadBase._secuencia)
        self._id = f"{self._prefijo}-{numero:04d}"

    @property
    def id(self):
        """ID de solo lectura."""
        return self._id

    @abstractmethod
    def descripcion(self):
        """Cada entidad debe definir cómo describirse."""

    def __repr__(self):
        return f"<{type(self).__name__} {self._id}>"