# Usa una imagen oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia archivos del proyecto al contenedor
COPY . .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone tu bot (no obligatorio para Discord)
EXPOSE 8080

# Comando para ejecutar el bot
CMD ["python", "main.py"]