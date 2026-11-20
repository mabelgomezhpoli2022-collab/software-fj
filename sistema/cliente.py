"""Modelo de cliente con validación de datos personales para Software FJ.

Los datos se guardan en atributos internos (`_nombre`, `_documento`, etc.) y
pasan por propiedades para validar su formato antes de asignarlos.
"""
import re

from .entidades import EntidadBase, exigir
from .excepciones import DatoInvalidoError

PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def enmascarar(documento):
    """Deja visibles solo los últimos 4 dígitos (ej. '1012345678' -> '******5678')."""
    texto = str(documento)
    return "*" * max(len(texto) - 4, 0) + texto[-4:]


class Cliente(EntidadBase):
    """Representa un cliente registrado en el sistema."""

    _prefijo = "CLI"

    def __init__(self, nombre, documento, email, telefono=None):
        super().__init__()
        # Asignamos vía propiedades para que cada campo se valide al entrar
        self.nombre = nombre
        self.documento = documento
        self.email = email
        self.telefono = telefono

    # Nombre: solo letras y espacios, mínimo 3 caracteres
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        texto = str(exigir(valor, "nombre")).strip()
        if len(texto) < 3 or not all(c.isalpha() or c.isspace() for c in texto):
            raise DatoInvalidoError(
                "El nombre necesita al menos 3 caracteres y solo puede tener letras y espacios."
            )
        self._nombre = " ".join(texto.split()).title()

    # Documento: entre 6 y 12 dígitos numéricos
    @property
    def documento(self):
        return self._documento

    @documento.setter
    def documento(self, valor):
        texto = str(exigir(valor, "documento")).strip()
        if not (texto.isdigit() and 6 <= len(texto) <= 12):
            raise DatoInvalidoError("El documento debe tener entre 6 y 12 dígitos.")
        self._documento = texto

    @property
    def documento_enmascarado(self):
        """Documento oculto parcialmente, útil para logs o pantallas."""
        return enmascarar(self._documento)

    # Correo electrónico: formato básico y normalizado en minúsculas
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        texto = str(exigir(valor, "email")).strip().lower()
        if not PATRON_EMAIL.match(texto):
            raise DatoInvalidoError(f"'{texto}' no parece un correo válido.")
        self._email = texto

    # Teléfono: opcional, de 7 a 15 dígitos, con '+' inicial opcional
    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor is None or not str(valor).strip():
            self._telefono = None
            return
        texto = str(valor).replace(" ", "").lstrip("+")
        if not (texto.isdigit() and 7 <= len(texto) <= 15):
            raise DatoInvalidoError(
                "El teléfono debe tener entre 7 y 15 dígitos (puede llevar '+' al inicio)."
            )
        self._telefono = texto

    def descripcion(self):
        return f"Cliente {self._nombre} (doc. {self.documento_enmascarado}, {self._email})"