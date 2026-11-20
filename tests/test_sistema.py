"""Pruebas unitarias para el sistema de Software FJ.

Correr desde la raíz del proyecto:
    python -m unittest discover -s tests -t .
"""
import unittest

from sistema.cliente import Cliente
from sistema.excepciones import (
    CalculoInconsistenteError,
    DatoInvalidoError,
    OperacionNoPermitidaError,
    ParametroFaltanteError,
    ReservaError,
    ServicioNoDisponibleError,
)
from sistema.gestor import SistemaFJ
from sistema.reserva import EstadoReserva, Reserva
from sistema.servicios import AsesoriaEspecializada, SalaReserva, Servicio


class TestCliente(unittest.TestCase):
    def test_normaliza_datos_al_crear_cliente(self):
        cliente = Cliente("ana   perez", "1012345678", "ANA@correo.com")
        self.assertEqual(cliente.nombre, "Ana Perez")
        self.assertEqual(cliente.email, "ana@correo.com")
        self.assertEqual(cliente.documento_enmascarado, "******5678")

    def test_rechaza_email_sin_formato_valido(self):
        with self.assertRaises(DatoInvalidoError):
            Cliente("Ana Perez", "1012345678", "sin-arroba")

    def test_rechaza_documento_vacio_o_none(self):
        with self.assertRaises(ParametroFaltanteError):
            Cliente("Ana Perez", None, "ana@correo.com")


class TestServicios(unittest.TestCase):
    def test_calcula_costo_base_sin_ajustes(self):
        self.assertEqual(SalaReserva("Sala A", 50000, 10).calcular_costo(2), 100000.0)

    def test_calcula_costo_con_impuesto_y_descuento(self):
        sala = SalaReserva("Sala A", 50000, 10)
        self.assertEqual(sala.calcular_costo(2, impuesto=0.19), 119000.0)
        self.assertEqual(sala.calcular_costo(2, descuento=0.10, impuesto=0.19), 107100.0)

    def test_rechaza_tarifa_negativa(self):
        with self.assertRaises(DatoInvalidoError):
            SalaReserva("Sala", -100, 10)

    def test_no_permite_instanciar_servicio_abstracto(self):
        with self.assertRaises(TypeError):
            Servicio("X", 100)

    def test_aplica_recargo_en_asesoria_avanzada(self):
        asesoria = AsesoriaEspecializada("Ase", 100000, "Nube", "avanzado")
        self.assertEqual(asesoria.calcular_costo(2), 240000.0)

    def test_rechaza_duracion_fuera_de_bloques_de_media_hora(self):
        with self.assertRaises(DatoInvalidoError):
            AsesoriaEspecializada("Ase", 100000, "Nube").validar_parametros(2.25)

    def test_falla_si_servicio_no_esta_disponible(self):
        sala = SalaReserva("Sala", 1000, 5)
        sala.disponible = False
        with self.assertRaises(ServicioNoDisponibleError):
            sala.calcular_costo(1)


class TestReserva(unittest.TestCase):
    def setUp(self):
        self.cliente = Cliente("Carla Ruiz", "52111222", "carla@correo.com")
        self.sala = SalaReserva("Sala B", 50000, 8)

    def test_flujo_normal_confirmar_y_procesar(self):
        reserva = Reserva(self.cliente, self.sala, 3)
        reserva.confirmar()
        reserva.procesar()
        self.assertEqual(reserva.estado, EstadoReserva.PROCESADA)
        self.assertEqual(reserva.costo, 178500.0)

    def test_no_procesa_si_no_esta_confirmada(self):
        reserva = Reserva(self.cliente, self.sala, 2)
        with self.assertRaises(OperacionNoPermitidaError):
            reserva.procesar()

    def test_encadena_error_si_duracion_es_invalida(self):
        with self.assertRaises(ReservaError) as contexto:
            Reserva(self.cliente, self.sala, 30)
        self.assertIsInstance(contexto.exception.__cause__, DatoInvalidoError)

    def test_no_cancela_reserva_ya_procesada(self):
        reserva = Reserva(self.cliente, self.sala, 1)
        reserva.confirmar()
        reserva.procesar()
        with self.assertRaises(OperacionNoPermitidaError):
            reserva.cancelar()

    def test_encadena_calculo_inconsistente_sin_cambiar_estado(self):
        class SalaConFallo(SalaReserva):
            def _costo_sin_ajustes(self, duracion):
                return -1.0

        reserva = Reserva(self.cliente, SalaConFallo("X", 1000, 2), 1)
        reserva.confirmar()
        with self.assertRaises(ReservaError) as contexto:
            reserva.procesar()
        self.assertIsInstance(contexto.exception.__cause__, CalculoInconsistenteError)
        # Si falla al procesar, debe seguir confirmada
        self.assertEqual(reserva.estado, EstadoReserva.CONFIRMADA)


class TestSistemaFJ(unittest.TestCase):
    def test_error_en_operacion_no_detiene_el_sistema(self):
        sistema = SistemaFJ()
        resultado = sistema.registrar_cliente("", "123456", "a@correo.com")
        self.assertFalse(resultado.ok)
        self.assertIsInstance(resultado.error, ParametroFaltanteError)
        # Verificamos que el sistema sigue operativo luego del fallo
        self.assertTrue(sistema.registrar_cliente("Ana Pérez", "1012345678", "ana@correo.com").ok)

    def test_crea_reserva_desde_el_gestor(self):
        sistema = SistemaFJ()
        sistema.registrar_cliente("Ana Pérez", "1012345678", "ana@correo.com")
        servicio = sistema.registrar_servicio(SalaReserva, "Sala", 50000, 10)
        self.assertTrue(sistema.crear_reserva("1012345678", servicio.valor.id, 2).ok)

    def test_captura_excepciones_inesperadas(self):
        class ServicioRoto(SalaReserva):
            def _costo_sin_ajustes(self, duracion):
                raise RuntimeError("fallo grave simulado")

        sistema = SistemaFJ()
        servicio = sistema.registrar_servicio(ServicioRoto, "Roto", 1000, 5)
        resultado = sistema.cotizar(servicio.valor.id, 1)
        self.assertFalse(resultado.ok)
        self.assertIn("inesperado", resultado.mensaje)


if __name__ == "__main__":
    unittest.main()