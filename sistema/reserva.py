"""Une cliente, servicio, duración y estado en el ciclo de vida de una reserva.

Maneja confirmación, cancelación y procesamiento validando transiciones de
estado y registrando lo que ocurre en el log.
"""
from enum import Enum

from .cliente import Cliente
from .entidades import EntidadBase
from .excepciones import (
    CalculoInconsistenteError,
    DatoInvalidoError,
    OperacionNoPermitidaError,
    ReservaError,
    ServicioNoDisponibleError,
    SoftwareFJError,
)
from .logger import configurar_logger
from .servicios import IMPUESTO_POR_DEFECTO, Servicio

log = configurar_logger()


class EstadoReserva(Enum):
    """Estados por los que puede pasar una reserva."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"


class Reserva(EntidadBase):
    """Reserva asociada a un cliente, un servicio y una duración."""

    _prefijo = "RES"

    def __init__(self, cliente, servicio, duracion):
        super().__init__()
        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("Se necesita un cliente válido para crear la reserva.")
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("Se necesita un servicio válido para crear la reserva.")
        try:
            servicio.validar_parametros(duracion)
        except SoftwareFJError as error:
            # Guardamos el error original como causa para no perder contexto
            raise ReservaError(f"No se pudo crear la reserva para '{servicio.nombre}': {error}") from error

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = float(duracion)
        self._estado = EstadoReserva.PENDIENTE
        self._costo = None
        log.info(
            "Reserva %s creada: %s en '%s' (duración %g)",
            self._id,
            cliente.nombre,
            servicio.nombre,
            self._duracion,
        )

    # Datos de solo lectura

    @property
    def estado(self):
        return self._estado

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def costo(self):
        return self._costo

    # Acciones sobre la reserva

    def confirmar(self):
        """Pasa la reserva de pendiente a confirmada."""
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"Solo se pueden confirmar reservas pendientes (ahora está en '{self._estado.value}')."
            )
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(
                f"No se puede confirmar: '{self._servicio.nombre}' no está disponible ahora."
            )
        self._estado = EstadoReserva.CONFIRMADA
        log.info("Reserva %s confirmada", self._id)

    def cancelar(self, motivo="Sin motivo especificado"):
        """Cancela la reserva, a menos que ya esté procesada o cancelada."""
        if self._estado in (EstadoReserva.PROCESADA, EstadoReserva.CANCELADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva que ya está '{self._estado.value}'."
            )
        self._estado = EstadoReserva.CANCELADA
        log.info("Reserva %s cancelada. Motivo: %s", self._id, motivo)

    def procesar(self):
        """Calcula el costo final con impuesto y marca la reserva como procesada."""
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError("Solo se pueden procesar reservas confirmadas.")
        try:
            self._costo = self._servicio.calcular_costo(self._duracion, impuesto=IMPUESTO_POR_DEFECTO)
        except CalculoInconsistenteError as error:
            # Conservamos el fallo de cálculo en __cause__ al envolverlo en ReservaError
            raise ReservaError(f"No se pudo procesar la reserva {self._id}.") from error
        else:
            self._estado = EstadoReserva.PROCESADA
            log.info("Reserva %s procesada. Costo total: %.2f", self._id, self._costo)
        finally:
            log.debug("Procesamiento de %s terminó en estado %s", self._id, self._estado.value)

    def descripcion(self):
        return (
            f"{self._id} | {self._cliente.nombre} | {self._servicio.nombre} | "
            f"{self._duracion:g} | {self._estado.value}"
        )