# Software FJ – Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto del curso **Programación (213023)** – Fase 4, Ejercicio 1 (Anexo 3).
Aplicación orientada a objetos en **Python 3.10+**, sin bases de datos. La
información vive en objetos y listas; los errores y eventos se registran en
un archivo de logs.

## Requisitos
- Python 3.10 o superior (no requiere librerías externas).

## Ejecución

```bash
# Simulación completa (30 operaciones válidas e inválidas)
python main.py

# Pruebas unitarias
python -m unittest discover -s tests -t .
```

Los eventos y errores se guardan en `logs/eventos.log`.

## Estructura

```
software_fj/
├── main.py                  # Simulación de operaciones (punto de entrada)
├── sistema/
│   ├── excepciones.py       # Jerarquía de excepciones personalizadas
│   ├── logger.py            # Configuración del archivo de logs
│   ├── entidades.py         # Clase abstracta EntidadBase
│   ├── cliente.py           # Clase Cliente (validaciones y encapsulación)
│   ├── servicios.py         # Clase abstracta Servicio + 3 especializaciones
│   ├── reserva.py           # Clase Reserva (confirmar, cancelar, procesar)
│   └── gestor.py            # SistemaFJ: coordina clientes, servicios y reservas
├── tests/
│   └── test_sistema.py      # Pruebas unitarias
└── logs/eventos.log         # Se genera al ejecutar
```

## Cómo se cumple cada requisito del Anexo 3

| Requisito | Dónde está |
|---|---|
| Clase abstracta de entidades generales | `EntidadBase` (`entidades.py`) |
| Clase `Cliente` con validaciones y datos encapsulados | `cliente.py`: propiedades con validación; documento enmascarado en salidas |
| Clase abstracta `Servicio` con al menos 3 servicios derivados | `servicios.py`: `SalaReserva`, `AlquilerEquipo`, `AsesoriaEspecializada` |
| Polimorfismo y métodos sobrescritos (costo, descripción, validación) | `validar_parametros`, `_costo_sin_ajustes` y `descripcion` en cada subclase |
| Clase `Reserva` con cliente, servicio, duración y estado | `reserva.py`: estados `Pendiente`, `Confirmada`, `Cancelada`, `Procesada` |
| Confirmación, cancelación y procesamiento con manejo de excepciones | `Reserva.confirmar()`, `cancelar()`, `procesar()` |
| Métodos sobrecargados | `Servicio.calcular_costo(duracion, impuesto=None, descuento=None)`: variantes con y sin impuesto/descuento |
| Excepciones personalizadas | `excepciones.py` (7 clases, todas heredan de `SoftwareFJError`) |
| `try/except`, `try/except/else`, `try/except/finally` | `gestor._ejecutar`, `Reserva.procesar`, `Reserva.__init__` |
| Encadenamiento de excepciones (`raise ... from`) | `Reserva.__init__`, `Reserva.procesar`, `servicios._a_numero` |
| Archivo de logs con errores y eventos | `logger.py` → `logs/eventos.log` |
| Continuar funcionando ante errores | `SistemaFJ._ejecutar` no deja escapar excepciones; `main.py` ejecuta 30 operaciones |
| Sin bases de datos | Toda la información se guarda en listas de objetos |

## Decisiones de diseño

- **Sobrecarga en Python:** Python no admite sobrecarga clásica, así que se
  simula con parámetros opcionales en `calcular_costo`.
- **Resultado uniforme:** las operaciones públicas de `SistemaFJ` devuelven un
  `Resultado` (`ok`, `mensaje`, `valor`, `error`) en lugar de lanzar excepciones
  hacia afuera.
- **Dos niveles de captura:** primero las excepciones del dominio
  (`SoftwareFJError`), y como último recurso cualquier `Exception`, que se
  registra con traza completa.
- **Privacidad:** los documentos se muestran enmascarados (`******5678`).
