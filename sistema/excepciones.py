"""Excepciones propias de Software FJ.

Todas cuelgan de `SoftwareFJError` para poder atrapar cualquier error del
dominio en un solo `except SoftwareFJError` cuando haga falta.
"""


class SoftwareFJError(Exception):
    """Error base del sistema; agrupa todas las excepciones del dominio."""


class DatoInvalidoError(SoftwareFJError):
    """Un dato no cumple con el formato o el rango esperado."""


class ParametroFaltanteError(SoftwareFJError):
    """Falta un parámetro obligatorio (viene en None o vacío)."""


class OperacionNoPermitidaError(SoftwareFJError):
    """La acción no se puede hacer en el estado actual o rompe una regla."""


class EntidadNoEncontradaError(SoftwareFJError):
    """No apareció el cliente, servicio o reserva que se estaba buscando."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio existe, pero ahora mismo no está disponible."""


class ReservaError(SoftwareFJError):
    """Algo falló al crear, confirmar, procesar o gestionar una reserva.

    Normalmente se lanza encadenando el error original con `raise ... from`.
    """


class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo de un costo dio un valor inválido o sin sentido."""