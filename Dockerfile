# Se utiliza una imagen base de Python 3.9
FROM python:3.9

# Se establece el directorio de trabajo
WORKDIR /app

# Se copian los archivos de la aplicación Flask al contenedor
COPY . .

# Se instalan las dependencias de la aplicación
RUN pip install -r requirements.txt

# Se expone el puerto 5000
EXPOSE 5000

# Se define el comando para iniciar la aplicación
CMD ["python", "run.py"]
