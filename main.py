"""Ejemplo de uso del sistema Software FJ.

En este archivo se prueban distintas situaciones del sistema:
registro de clientes, creación de servicios, cotizaciones y reservas.
También se incluyen algunos datos incorrectos para comprobar que los
errores se manejen sin detener toda la ejecución.

Para iniciar la simulación, ejecutar: python main.py
"""

from sistema.gestor import SistemaFJ
from sistema.logger import ARCHIVO_LOG
from sistema.servicios import (
    AlquilerEquipo,
    AsesoriaEspecializada,
    SalaReserva,
    Servicio,
)


class ServicioDefectuoso(SalaReserva):
    """Servicio de prueba que devuelve un costo incorrecto a propósito."""

    def _costo_sin_ajustes(self, duracion):
        # Se usa un valor negativo para comprobar el manejo de este error.
        return -1.0


def obtener_id(resultado):
    """Obtiene el identificador si la operación salió bien."""
    if resultado.ok:
        return resultado.valor.id
    return None


def mostrar_resultado(numero, descripcion, resultado):
    """Muestra en pantalla cómo terminó cada operación."""
    estado = "OK   " if resultado.ok else "ERROR"

    print(f"{numero:>2}. [{estado}] {descripcion}")
    print(f"        {resultado.mensaje}")

    if resultado.ok and resultado.valor is not None:
        dato = resultado.valor

        if hasattr(dato, "id"):
            print(f"        -> Identificador: {dato.id}")
        else:
            print(f"        -> Valor: {dato:,.2f}")


def main():
    sistema = SistemaFJ("Software FJ")
    numero_operacion = 0

    # Esta función permite llevar el orden de las operaciones y mostrar
    # el resultado sin repetir el mismo código en cada prueba.
    def ejecutar_paso(descripcion, resultado):
        nonlocal numero_operacion
        numero_operacion += 1
        mostrar_resultado(numero_operacion, descripcion, resultado)
        return resultado

    print("=" * 72)
    print("SOFTWARE FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas")
    print("=" * 72)

    # Primero se prueban los registros de clientes.
    print("\n--- Clientes ---")

    ejecutar_paso(
        "Registrar cliente válido",
        sistema.registrar_cliente(
            "Ana Pérez", "1012345678", "ana.perez@correo.com", "+57 300 1234567"
        ),
    )
    ejecutar_paso(
        "Cliente con correo inválido",
        sistema.registrar_cliente("Luis Gómez", "1098765432", "luis-correo-invalido"),
    )
    ejecutar_paso(
        "Cliente sin nombre (parámetro faltante)",
        sistema.registrar_cliente("", "2000000", "x@correo.com"),
    )
    ejecutar_paso(
        "Cliente con documento que contiene letras",
        sistema.registrar_cliente("Pedro Díaz", "AB12CD", "pedro@correo.com"),
    )
    ejecutar_paso(
        "Registrar segundo cliente válido",
        sistema.registrar_cliente("Carla Ruiz", "52111222", "carla.ruiz@correo.com"),
    )
    ejecutar_paso(
        "Cliente con documento duplicado",
        sistema.registrar_cliente("Ana Duplicada", "1012345678", "otra@correo.com"),
    )

    # Después se crean servicios y se revisan algunos datos incorrectos.
    print("\n--- Servicios ---")

    sala = ejecutar_paso(
        "Crear servicio correcto: sala",
        sistema.registrar_servicio(SalaReserva, "Sala Innovación", 50000, 10),
    )
    ejecutar_paso(
        "Crear servicio incorrecto: tarifa negativa",
        sistema.registrar_servicio(SalaReserva, "Sala Fantasma", -100, 10),
    )
    equipos = ejecutar_paso(
        "Crear servicio correcto: alquiler de equipos",
        sistema.registrar_servicio(AlquilerEquipo, "Paquete Portátiles", 25000, 5),
    )
    ejecutar_paso(
        "Crear servicio incorrecto: unidades fuera de rango",
        sistema.registrar_servicio(AlquilerEquipo, "Paquete Vacío", 25000, 0),
    )
    asesoria = ejecutar_paso(
        "Crear servicio correcto: asesoría avanzada",
        sistema.registrar_servicio(
            AsesoriaEspecializada, "Asesoría Cloud", 90000, "Nube", "avanzado"
        ),
    )
    servicio_defectuoso = ejecutar_paso(
        "Crear servicio con fallo interno simulado",
        sistema.registrar_servicio(
            ServicioDefectuoso, "Sala Defectuosa", 30000, 4
        ),
    )
    ejecutar_paso(
        "Crear servicio abstracto (no permitido)",
        sistema.registrar_servicio(Servicio, "Genérico", 1000),
    )

    # Se realiza una cotización para probar el cálculo con descuento e IVA.
    print("\n--- Cotizaciones (sobrecarga de cálculo de costos) ---")
    ejecutar_paso(
        "Cotizar 2 horas con descuento del 10 % e IVA",
        sistema.cotizar(obtener_id(sala), 2, descuento=0.10),
    )

    # Por último, se prueban las reservas y sus diferentes estados.
    print("\n--- Reservas ---")

    reserva_1 = ejecutar_paso(
        "Crear reserva exitosa (3 h en sala)",
        sistema.crear_reserva("1012345678", obtener_id(sala), 3),
    )
    ejecutar_paso(
        "Confirmar reserva",
        sistema.confirmar_reserva(obtener_id(reserva_1)),
    )
    ejecutar_paso(
        "Procesar reserva",
        sistema.procesar_reserva(obtener_id(reserva_1)),
    )
    ejecutar_paso(
        "Reserva con cliente inexistente",
        sistema.crear_reserva("99999999", obtener_id(sala), 2),
    )
    ejecutar_paso(
        "Reserva con duración fuera de rango",
        sistema.crear_reserva("52111222", obtener_id(sala), 30),
    )
    ejecutar_paso(
        "Asesoría con duración no válida (2.25 h)",
        sistema.crear_reserva("52111222", obtener_id(asesoria), 2.25),
    )

    reserva_2 = ejecutar_paso(
        "Reserva sobre servicio con fallo interno",
        sistema.crear_reserva("52111222", obtener_id(servicio_defectuoso), 2),
    )
    ejecutar_paso(
        "Confirmar reserva sobre servicio con fallo",
        sistema.confirmar_reserva(obtener_id(reserva_2)),
    )
    ejecutar_paso(
        "Procesar reserva con cálculo inconsistente",
        sistema.procesar_reserva(obtener_id(reserva_2)),
    )
    ejecutar_paso(
        "Desactivar servicio de alquiler",
        sistema.cambiar_disponibilidad(obtener_id(equipos), False),
    )

    reserva_3 = ejecutar_paso(
        "Reserva sobre servicio no disponible (creación)",
        sistema.crear_reserva("52111222", obtener_id(equipos), 2),
    )
    ejecutar_paso(
        "Confirmar reserva con servicio no disponible",
        sistema.confirmar_reserva(obtener_id(reserva_3)),
    )
    ejecutar_paso(
        "Cancelar reserva ya procesada",
        sistema.cancelar_reserva(obtener_id(reserva_1)),
    )

    reserva_4 = ejecutar_paso(
        "Reserva válida de asesoría (1.5 h)",
        sistema.crear_reserva("52111222", obtener_id(asesoria), 1.5),
    )
    ejecutar_paso(
        "Cancelar reserva pendiente",
        sistema.cancelar_reserva(
            obtener_id(reserva_4), "Cliente cambió de fecha"
        ),
    )
    ejecutar_paso(
        "Confirmar reserva inexistente",
        sistema.confirmar_reserva("RES-9999"),
    )

    print("\n" + sistema.reporte())
    print(f"\nRegistro de eventos y errores: {ARCHIVO_LOG}")
    print("La simulación terminó sin interrupciones.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecución interrumpida por el usuario.")
