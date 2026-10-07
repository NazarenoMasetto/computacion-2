#!/usr/bin/env python3
"""Ejercicio 3.3 - Lector lazy con buffer (BufferedReader).

Lee el archivo en bloques de `buffer_size` bytes pero entrega líneas
completas. Si un bloque corta una línea, el pedazo queda guardado y se une
con el bloque siguiente. Las líneas se entregan con su '\\n' final (igual que
al iterar un archivo normal). Se puede usar directo en un for o como
context manager.
"""

import codecs
from typing import Iterator


class BufferedReader:
    """Itera las líneas de un archivo leyendo de a `buffer_size` bytes."""

    def __init__(self, ruta: str, buffer_size: int = 8192, encoding: str = "utf-8") -> None:
        if buffer_size < 1:
            raise ValueError("buffer_size debe ser >= 1")
        self.ruta = ruta
        self.buffer_size = buffer_size
        self.encoding = encoding
        self._archivo = None

    def __enter__(self) -> "BufferedReader":
        self._archivo = open(self.ruta, "rb")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self._archivo is not None:
            self._archivo.close()
            self._archivo = None

    def __iter__(self) -> Iterator[str]:
        # Si no se usó con 'with', abrimos y cerramos nosotros
        if self._archivo is None:
            with open(self.ruta, "rb") as f:
                yield from self._lineas(f)
        else:
            yield from self._lineas(self._archivo)

    def _lineas(self, f) -> Iterator[str]:
        # El decoder incremental evita romper caracteres multibyte (ej: 'ñ')
        # que queden partidos entre dos bloques.
        decoder = codecs.getincrementaldecoder(self.encoding)()
        pendiente = ""
        while True:
            bloque = f.read(self.buffer_size)
            if not bloque:
                break
            pendiente += decoder.decode(bloque)
            # Entregamos todas las líneas completas que haya en el buffer
            inicio = 0
            while (pos := pendiente.find("\n", inicio)) != -1:
                yield pendiente[inicio:pos + 1]
                inicio = pos + 1
            pendiente = pendiente[inicio:]  # resto incompleto para el próximo bloque
        pendiente += decoder.decode(b"", final=True)
        if pendiente:
            yield pendiente  # última línea sin '\n'


if __name__ == "__main__":
    import os
    import tempfile

    contenido = "".join(
        f"{'ERROR' if i % 7 == 0 else 'INFO'} línea {i} con ñandú y acentos áéí\n"
        for i in range(200)
    ) + "última sin salto"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        tmp.write(contenido)

    try:
        # Probamos varios tamaños de buffer, incluso ridículamente chicos
        esperado = contenido.splitlines(keepends=True)
        for tam in (1, 2, 3, 7, 64, 8192):
            assert list(BufferedReader(tmp.name, buffer_size=tam)) == esperado, tam
        print("Mismas líneas que splitlines() con buffers de 1, 2, 3, 7, 64 y 8192 bytes. OK")

        errores = [l for l in BufferedReader(tmp.name, buffer_size=16) if "ERROR" in l]
        print(f"Líneas con ERROR: {len(errores)}; primera: {errores[0]!r}")

        with BufferedReader(tmp.name) as reader:
            for i, linea in enumerate(reader):
                if i >= 3:
                    break
                print(linea, end="")
    finally:
        os.remove(tmp.name)
