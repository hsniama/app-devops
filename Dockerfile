# ======================================
# Dockerfile Hardenizado - DevOps Microservice
# ======================================

# === Paso 1: Usar imagen base liviana y actualizada ===
# - Reduce exposición a CVEs del sistema base (glibc, krb5, coreutils)
FROM python:3.13-alpine

# === Paso 2: Crear usuario y grupo no-root ===
# - Evita ejecución como root (remediación Trivy y Docker Scout)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --uid 10001 --home /home/appuser appuser

# === Paso 3: Crear directorio de trabajo con permisos seguros ===
WORKDIR /app
RUN chown appuser:appgroup /app

# === Paso 4: Copiar e instalar dependencias actualizadas ===
COPY requirements.txt .
# - Se actualizan versiones de gunicorn y h11 en requirements.txt previamente
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# === Paso 4.1: instalar curl para el HEALTHCHECK ===
RUN apk add --no-cache curl


# === Paso 5: Copiar código fuente ===
COPY . .

# === Paso 6: Variables de entorno seguras y configurables ===
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JWT_EXP_MINUTES=60 

# === Paso 7: Limpieza del sistema y eliminación de posibles paquetes vulnerables ===
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# === Paso 8: HEALTHCHECK robusto ===
# - --retries: reintenta antes de marcar unhealthy
# - --start-period: da tiempo extra al arranque inicial
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -fsS http://127.0.0.1:8000/healthz >/dev/null || exit 1

# === Paso 9: Exponer puerto usado por Gunicorn/Uvicorn ===
EXPOSE 8000

# === Paso 10: Ejecutar como usuario no-root ===
USER appuser

# === Paso 11: Comando de producción con Gunicorn ===
CMD ["gunicorn", "app.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
# Nota en -w defino el numero de workers. está solo 1 para que funcione el used_tokens Si quiero multi workers necesito
# almacenamiento compartido para el estado de los tokens usados, por ejemplo redis o alguna BBDD.