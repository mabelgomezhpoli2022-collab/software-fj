"""Servicios disponibles en Software FJ.

Define la clase base `Servicio` y tres tipos concretos (`SalaReserva`,
`AlquilerEquipo` y `AsesoriaEspecializada`), cada uno con sus propias reglas
de duración y cálculo de costo. `calcular_costo` admite impuesto y descuento
opcionales para cubrir distintos escenarios de cobro.
"""
import math
from abc import ABC, abstractmethod

from .entidades import EntidadBase, exigir
from .excepciones import (
    CalculoInconsistenteError,
    DatoInvalidoError,
    ServicioNoDisponibleError,
)

IMPUESTO_POR_DEFECTO = 0.19  # IVA base del 19 %

# Validaciones numéricas


def _a_numero(valor, campo):
    """Pasa el valor a float y avisa con claridad si no sirve como número."""
    exigir(valor, campo)
    if isinstance(valor, bool):
        raise DatoInvalidoError(f"'{campo}' debe ser un número, no un booleano.")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        # Conservamos la causa original por si toca depurar
        raise DatoInvalidoError(f"'{campo}' no parece un número válido ({valor!r}).") from error
    if not math.isfinite(numero):
        raise DatoInvalidoError(f"'{campo}' debe ser un número finito.")
    return numero


def _validar_rango(valor, minimo, maximo, campo):
    numero = _a_numero(valor, campo)
    if not minimo <= numero <= maximo:
        raise DatoInvalidoError(
            f"'{campo}' tiene que estar entre {minimo:g} y {maximo:g} (llegó {numero:g})."
        )
    return numero


def _validar_entero(valor, minimo, maximo, campo):
    numero = _a_numero(valor, campo)
    if not numero.is_integer():
        raise DatoInvalidoError(f"'{campo}' debe ser un número entero.")
    return int(_validar_rango(numero, minimo, maximo, campo))


# Clase base de servicios


class Servicio(EntidadBase, ABC):
    """Base común para cualquier servicio que se pueda reservar o cotizar."""

    _prefijo = "SRV"

    def __init__(self, nombre, tarifa_base):
        super().__init__()
        self._nombre = " ".join(str(exigir(nombre, "nombre del servicio")).split())
        self._tarifa_base = _validar_rango(tarifa_base, 0.01, 10_000_000, "tarifa base")
        self._disponible = True

    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_base(self):
        return self._tarifa_base

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        if not isinstance(valor, bool):
            raise DatoInvalidoError("La disponibilidad solo acepta True o False.")
        self._disponible = valor

    @abstractmethod
    def validar_parametros(self, duracion):
        """Revisa que la duración sea válida según las reglas de cada servicio."""

    @abstractmethod
    def _costo_sin_ajustes(self, duracion):
        """Calcula el valor base según la duración, antes de descuentos o impuestos."""

    def calcular_costo(self, duracion, impuesto=None, descuento=None):
        """Calcula el total a cobrar según duración, descuento e impuesto opcionales.

        Ejemplos de uso:
            calcular_costo(d)                 # solo costo base
            calcular_costo(d, impuesto=0.19)  # aplicando impuesto
            calcular_costo(d, descuento=0.10) # aplicando descuento
            calcular_costo(d, 0.19, 0.10)     # descuento e impuesto juntos
        """
        if not self._disponible:
            raise ServicioNoDisponibleError(
                f"'{self._nombre}' no está disponible por ahora."
            )
        self.validar_parametros(duracion)
        subtotal = self._costo_sin_ajustes(duracion)
        if not math.isfinite(subtotal) or subtotal <= 0:
            raise CalculoInconsistenteError(
                f"El subtotal ({subtotal}) de '{self._nombre}' no tiene sentido."
            )
        if descuento is not None:
            subtotal *= 1 - _validar_rango(descuento, 0, 0.99, "descuento")
        if impuesto is not None:
            subtotal *= 1 + _validar_rango(impuesto, 0, 1, "impuesto")
        return round(subtotal, 2)


# Tipos de servicio


class SalaReserva(Servicio):
    """Alquiler de salas por horas (entre 1 y 12 horas)."""

    def __init__(self, nombre, tarifa_hora, capacidad):
        super().__init__(nombre, tarifa_hora)
        self._capacidad = _validar_entero(capacidad, 1, 500, "capacidad")

    @property
    def capacidad(self):
        return self._capacidad

    def validar_parametros(self, duracion):
        _validar_rango(duracion, 1, 12, "horas")

    def _costo_sin_ajustes(self, duracion):
        return self.tarifa_base * float(duracion)

    def descripcion(self):
        return (
            f"Sala '{self.nombre}' - capacidad {self._capacidad} personas - "
            f"{self.tarifa_base:,.0f} COP por hora"
        )


class AlquilerEquipo(Servicio):
    """Alquiler de equipos por días completos (de 1 a 30 días)."""

    def __init__(self, nombre, tarifa_dia, unidades):
        super().__init__(nombre, tarifa_dia)
        self._unidades = _validar_entero(unidades, 1, 50, "unidades")

    @property
    def unidades(self):
        return self._unidades

    def validar_parametros(self, duracion):
        _validar_entero(duracion, 1, 30, "días")

    def _costo_sin_ajustes(self, duracion):
        return self.tarifa_base * float(duracion) * self._unidades

    def descripcion(self):
        return (
            f"Alquiler '{self.nombre}' - {self._unidades} equipos - "
            f"{self.tarifa_base:,.0f} COP por día y equipo"
        )


class AsesoriaEspecializada(Servicio):
    """Asesoría por horas en bloques de 0.5 (mínimo 0.5, máximo 8 horas).

    Si el nivel es 'avanzado', se suma un 20 % de recargo.
    """

    NIVELES = ("basico", "avanzado")
    RECARGO_AVANZADO = 0.20

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="basico"):
        super().__init__(nombre, tarifa_hora)
        self._especialidad = str(exigir(especialidad, "especialidad")).strip()
        if nivel not in self.NIVELES:
            raise DatoInvalidoError(f"El nivel debe ser uno de estos: {self.NIVELES}.")
        self._nivel = nivel

    def validar_parametros(self, duracion):
        horas = _validar_rango(duracion, 0.5, 8, "horas")
        if (horas * 2) % 1 != 0:
            raise DatoInvalidoError(
                "Las asesorías van en bloques de media hora (0.5, 1, 1.5, etc.)."
            )

    def _costo_sin_ajustes(self, duracion):
        factor = 1 + self.RECARGO_AVANZADO if self._nivel == "avanzado" else 1
        return self.tarifa_base * float(duracion) * factor

    def descripcion(self):
        return (
            f"Asesoría '{self.nombre}' en {self._especialidad} (nivel {self._nivel}) - "
            f"{self.tarifa_base:,.0f} COP por hora"
        )