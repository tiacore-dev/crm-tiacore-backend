import os
import subprocess
import tempfile


def convert_to_pdf(file_bytes: bytes, input_ext: str) -> bytes:
    # Создаём временную директорию
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"input.{input_ext}")
        output_path = os.path.join(tmpdir, "input.pdf")

        # Сохраняем входной файл
        with open(input_path, "wb") as f:
            f.write(file_bytes)

        # Запускаем LibreOffice в headless-режиме
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdir,
                input_path,
            ],
            check=True,
        )

        # Читаем PDF-файл и возвращаем его байты
        with open(output_path, "rb") as f:
            return f.read()
