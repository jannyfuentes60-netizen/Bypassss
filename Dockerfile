# Usamos una versión estable de Python
FROM python:3.11-slim

# Instalamos ffmpeg y dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg libavcodec-extra && apt-get clean

# Directorio de trabajo
WORKDIR /app

# Copiamos archivos
COPY . .

# Instalamos librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para arrancar
CMD ["python", "main.py"]
