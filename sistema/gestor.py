"""Coordina clientes, servicios y reservas dentro de Software FJ.

Ninguna operación pública deja escapar excepciones hacia afuera: cada una
regresa un `Resultado` con el estado, un mensaje legible y deja registro en
los logs.
"""
import inspect
from collections import Counter
from dataclasses import dataclass
from typing import Any

from .cliente import Cliente
from .entidades import exigir
from .excepciones import (
    DatoInvalidoError,
    EntidadNoEncontradaError,
    OperacionNoPermitidaError,
    SoftwareFJError,
)
from .logger import configurar_logger
from .reserva import Reserva
from .servicios import IMPUESTO_POR_DEFECTO, Servicio


@dataclass
class Resultado:
    """Respuesta estándar de lo que ocurrió al ejecutar una operación."""

    ok: bool
    mensaje: str
    valor: Any = None
    error: Exception | None = None


class SistemaFJ:
    """Núcleo del sistema; mantiene en memoria clientes, servicios y reservas."""

    def __init__(self, nombre_empresa="Software FJ"):
        self.nombre_empresa = nombre_empresa
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []
        self._log = configurar_logger()
        self._operaciones = 0
        self._fallidas = 0

    # Ejecución segura

    def _ejecutar(self, nombre_operacion, funcion, *args, **kwargs):
        """Corre una operación y atrapa errores para que el flujo no se caiga."""
        self._operaciones += 1
        try:
            valor = funcion(*args, **kwargs)
        except SoftwareFJError as error:
            # Error conocido del dominio (validación o regla de negocio)
            self._fallidas += 1
            self._log.error("%s rechazada: %s [%s]", nombre_operacion, error, type(error).__name__)
            return Resultado(False, str(error), error=error)
        except Exception as error:
            # Algo imprevisto: guardamos el traceback completo para investigar
            self._fallidas += 1
            self._log.exception("%s: error inesperado", nombre_operacion)
            return Resultado(False, f"Ocurrió un error inesperado: {error}", error=error)
        self._log.info("%s realizada correctamente", nombre_operacion)
        return Resultado(True, "Listo, operación completada.", valor)

    # Clientes

    def registrar_cliente(self, nombre, documento, email, telefono=None):
        return self._ejecutar(
            "Registrar cliente",
            self._registrar_cliente,
            nombre,
            documento,
            email,
            telefono,
        )

    def _registrar_cliente(self, nombre, documento, email, telefono):
        cliente = Cliente(nombre, documento, email, telefono)
        if any(c.documento == cliente.documento for c in self._clientes):
            raise OperacionNoPermitidaError(
                f"Ya hay un cliente registrado con el documento {cliente.documento_enmascarado}."
            )
        self._clientes.append(cliente)
        return cliente

    # Servicios

    def registrar_servicio(self, clase_servicio, *args, **kwargs):
        """Instancia y registra un servicio del tipo indicado.

        Por ejemplo: registrar_servicio(SalaReserva, "Sala A", 50000, 10)
        """
        return self._ejecutar(
            "Registrar servicio",
            self._registrar_servicio,
            clase_servicio,
            *args,
            **kwargs,
        )

    def _registrar_servicio(self, clase_servicio, *args, **kwargs):
        if not (isinstance(clase_servicio, type) and issubclass(clase_servicio, Servicio)):
            raise DatoInvalidoError("Eso no corresponde a un tipo de servicio válido.")
        if inspect.isabstract(clase_servicio):
            raise DatoInvalidoError(
                f"'{clase_servicio.__name__}' es abstracta; pasa una clase de servicio concreta."
            )
        servicio = clase_servicio(*args, **kwargs)
        if any(s.nombre.lower() == servicio.nombre.lower() for s in self._servicios):
            raise OperacionNoPermitidaError(f"Ya existe un servicio llamado '{servicio.nombre}'.")
        self._servicios.append(servicio)
        return servicio

    def cambiar_disponibilidad(self, id_servicio, disponible):
        return self._ejecutar(
            "Cambiar disponibilidad",
            self._cambiar_disponibilidad,
            id_servicio,
            disponible,
        )

    def _cambiar_disponibilidad(self, id_servicio, disponible):
        servicio = self._buscar_servicio(id_servicio)
        servicio.disponible = disponible
        return servicio

    def cotizar(self, id_servicio, duracion, descuento=None):
        """Calcula el precio final del servicio (con impuesto y descuento si aplica)."""
        return self._ejecutar(
            "Cotizar servicio",
            self._cotizar,
            id_servicio,
            duracion,
            descuento,
        )

    def _cotizar(self, id_servicio, duracion, descuento):
        servicio = self._buscar_servicio(id_servicio)
        return servicio.calcular_costo(duracion, impuesto=IMPUESTO_POR_DEFECTO, descuento=descuento)

    # Reservas

    def crear_reserva(self, documento_cliente, id_servicio, duracion):
        return self._ejecutar(
            "Crear reserva",
            self._crear_reserva,
            documento_cliente,
            id_servicio,
            duracion,
        )

    def _crear_reserva(self, documento_cliente, id_servicio, duracion):
        cliente = self._buscar_cliente(documento_cliente)
        servicio = self._buscar_servicio(id_servicio)
        reserva = Reserva(cliente, servicio, duracion)
        self._reservas.append(reserva)
        return reserva

    def confirmar_reserva(self, id_reserva):
        return self._ejecutar("Confirmar reserva", self._operar_reserva, id_reserva, "confirmar")

    def procesar_reserva(self, id_reserva):
        return self._ejecutar("Procesar reserva", self._operar_reserva, id_reserva, "procesar")

    def cancelar_reserva(self, id_reserva, motivo="Cancelada por el cliente"):
        return self._ejecutar("Cancelar reserva", self._cancelar_reserva, id_reserva, motivo)

    def _operar_reserva(self, id_reserva, accion):
        reserva = self._buscar_reserva(id_reserva)
        if accion == "confirmar":
            reserva.confirmar()
        else:
            reserva.procesar()
        return reserva

    def _cancelar_reserva(self, id_reserva, motivo):
        reserva = self._buscar_reserva(id_reserva)
        reserva.cancelar(motivo)
        return reserva

    # Búsquedas internas (lanzan excepción si no encuentran nada)

    def _buscar_cliente(self, documento):
        exigir(documento, "documento del cliente")
        for cliente in self._clientes:
            if cliente.documento == str(documento).strip():
                return cliente
        raise EntidadNoEncontradaError("No se encontró ningún cliente con ese documento.")

    def _buscar_servicio(self, id_servicio):
        exigir(id_servicio, "id del servicio")
        for servicio in self._servicios:
            if servicio.id == str(id_servicio).strip():
                return servicio
        raise EntidadNoEncontradaError(f"No hay ningún servicio con id '{id_servicio}'.")

    def _buscar_reserva(self, id_reserva):
        exigir(id_reserva, "id de la reserva")
        for reserva in self._reservas:
            if reserva.id == str(id_reserva).strip():
                return reserva
        raise EntidadNoEncontradaError(f"No hay ninguna reserva con id '{id_reserva}'.")

    # Consultas

    @property
    def clientes(self):
        return tuple(self._clientes)

    @property
    def servicios(self):
        return tuple(self._servicios)

    @property
    def reservas(self):
        return tuple(self._reservas)

    def reporte(self):
        """Devuelve un resumen rápido del estado del sistema."""
        estados = Counter(r.estado.value for r in self._reservas)
        lineas = [
            f"=== Resumen de {self.nombre_empresa} ===",
            f"Clientes registrados : {len(self._clientes)}",
            f"Servicios registrados: {len(self._servicios)}",
            f"Reservas creadas     : {len(self._reservas)}",
        ]
        lineas += [f"  - {estado}: {cantidad}" for estado, cantidad in estados.items()]
        lineas.append(f"Operaciones ejecutadas: {self._operaciones} (fallidas: {self._fallidas})")
        return "\n".join(lineas)