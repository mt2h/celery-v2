# CELERY - GUÍA PRÁCTICA
# ======================================

## 📋 ESTRUCTURA DEL PROYECTO

```
.
├── docker-compose.yml                 # Stack local con todos los servicios
├── app/
│   ├── Dockerfile                     # Imagen de la app + workers
│   ├── requirements.txt               # Dependencias Python
│   ├── celeryconfig.py                # Configuración optimizada de Celery
│   ├── __init__.py                    # Inicializa Celery
│   ├── main.py                        # FastAPI app + endpoints
│   ├── tasks.py                       # Tareas (CPU-bound, I/O-bound, quick)
│   ├── models.py                      # SQLAlchemy models
│   └── database.py                    # Conexión DB
├── monitoring/
│   ├── prometheus.yml                 # Config de Prometheus
│   ├── telegraf.conf                  # Config de Telegraf (métricas Docker)
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── prometheus-ds.yml
│           └── dashboards/
│               └── celery-dashboard.json
```

## 🚀 PASO 1: DOCKER COMPOSE LOCAL

### Requisitos
```bash
docker --version    # >= 20.10
docker-compose --version  # >= 1.29
```

### Pasos para ejecutar
```bash
# 0. Dar permisos al socket de Docker (requerido para Telegraf en Fedora/SELinux)
sudo chmod 666 /var/run/docker.sock

# 1. Build de la imagen
docker-compose build

# 2. Start de todos los servicios
docker-compose up -d

# 3. Esperar a que todo esté healthy (30 segundos aprox)
docker-compose ps

# 4. Inicializar la DB (crear tablas)
docker-compose exec app python -c "from app.database import init_db; init_db()"
```

## 📊 ACCESO A SERVICIOS (Docker Compose)

| Servicio | URL | Usuario/Pass |
|----------|-----|--------------|
| **FastAPI** | http://localhost:8000 | - |
| **Swagger Docs** | http://localhost:8000/docs | - |
| **Metrics** | http://localhost:8000/metrics | - |
| **Flower** (Celery monitor) | http://localhost:5555 | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Redis CLI** | `docker-compose exec redis redis-cli` | - |
| **Postgres CLI** | `docker-compose exec postgres psql -U celery_user -d celery_db` | - |

## 🧪 TESTING EN DOCKER COMPOSE

### Endpoint de prueba rápida
```bash
# Terminal 1: Ver logs de workers
docker-compose logs -f celery_worker_default celery_worker_heavy

# Terminal 2: Disparar tareas
curl -X POST http://localhost:8000/task/quick?message=test1
curl -X POST http://localhost:8000/task/io?delay=3
curl -X POST http://localhost:8000/task/cpu?duration=5

# Ver status de una tarea
curl http://localhost:8000/task/{task_id}

# Estadísticas
curl http://localhost:8000/tasks/stats

# Bulk test (disparar muchas tareas)
curl -X POST "http://localhost:8000/task/bulk?cpu_count=3&io_count=5&quick_count=10"
```

### Observar en Flower
1. Abre http://localhost:5555
2. Ve a "Tasks" para ver ejecución en tiempo real
3. Ve a "Workers" para ver estado de workers y métricas

### Observar en Grafana (Recomendado)
1. Abre http://localhost:3000 (usuario: admin / contraseña: admin)
2. Ve a Dashboards → Celery Workers Dashboard
3. Ajusta el rango de tiempo a "Last 5 minutes"
4. Dispara tareas y ve los gráficos en tiempo real:
   - Memoria por contenedor
   - CPU por contenedor
   - Métricas de Celery (tasks ejecutadas, duración, etc.)
5. Observa cómo la memoria de los workers sube/baja (efecto de max_memory_per_child)

## 🔍 VERIFICAR CONFIGURACIÓN OPTIMIZADA EN ACCIÓN

### 1. Fair Dispatch (prefetch_multiplier=1)
```bash
# Terminal 1: Ver logs en vivo
docker-compose logs -f celery_worker_default

# Terminal 2: Dispara una tarea PESADA que tome 30 segundos
curl -X POST http://localhost:8000/task/cpu?duration=30

# Terminal 3: MIENTRAS ESTÁ EN PROGRESO, dispara muchas tareas RÁPIDAS
for i in {1..20}; do
  curl -X POST "http://localhost:8000/task/quick?message=quick_$i" &
done
wait

# RESULTADO ESPERADO:
# - Sin optimización: Las 20 tareas rápidas se quedan en cola esperando
# - Con prefetch_multiplier=1: Las rápidas se distribuyen a los otros workers
# - Ver en Flower: El worker_default no se "apodera" de todas
```

### 2. Memory Recycling (max_memory_per_child)
```bash
# Terminal 1: Monitorear memoria de un worker
docker stats celery_worker_default --no-stream

# Terminal 2: Dispara muchas tareas CPU-bound seguidas
for i in {1..50}; do
  curl -X POST http://localhost:8000/task/cpu?duration=2 &
done

# RESULTADO ESPERADO:
# - La memoria del worker NO crece indefinidamente
# - Cada 500 tareas, el proceso se reinicia (ves el salto en Prometheus)
# - En Grafana verás la forma de "onda" en memory usage
```

### 3. Split de Colas
```bash
# Ver qué colas existen
docker-compose exec redis redis-cli LLEN celery

# Ver workers y sus colas asociadas
curl http://localhost:5555/api/workers  # Flower API

# Disparar a diferentes colas
curl -X POST http://localhost:8000/task/cpu      # Va a "heavy"
curl -X POST http://localhost:8000/task/io       # Va a "default"
curl -X POST http://localhost:8000/task/quick    # Va a "default"

# Ver en Flower que cada tarea va al worker correcto
```

## 🔧 AJUSTAR CONFIGURACIÓN PARA TESTING

Si quieres experimentar CON vs SIN optimizaciones:

### Opción A: Sin Fair Dispatch (para ver el problema)
1. Edita `app/celeryconfig.py` y **comenta** estas líneas:
```python
# task_acks_late = True
# worker_prefetch_multiplier = 1
```

2. Aplica los cambios reconstruyendo y recreando los contenedores:
```bash
docker-compose up -d --build --force-recreate app celery_worker_default celery_worker_heavy
```

3. Ahora prueba:
```bash
# Dispara una tarea pesada
curl -X POST http://localhost:8000/task/cpu?duration=30

# Mientras está en progreso, dispara muchas rápidas
for i in {1..20}; do
  curl -X POST "http://localhost:8000/task/quick?message=quick_$i" &
done
```

**RESULTADO:** Las 20 tareas rápidas se quedan esperando (problema!)

### Opción B: Sin Memory Recycling
1. Edita `app/celeryconfig.py` y **comenta** estas líneas:
```python
# worker_max_tasks_per_child = 500
# worker_max_memory_per_child = 150000
```

2. Aplica los cambios:
```bash
docker-compose up -d --build --force-recreate app celery_worker_default celery_worker_heavy
```

3. Dispara 500+ tareas CPU-bound y observa en Grafana:
```bash
for i in {1..500}; do
  curl -X POST http://localhost:8000/task/cpu?duration=2 &
done
```

**RESULTADO:** La memoria crece sin parar (memory leak aparente)

### Restaurar configuración optimizada
Descomenta las líneas en `app/celeryconfig.py` y aplica los cambios:
```bash
docker-compose up -d --build --force-recreate app celery_worker_default celery_worker_heavy
```

## 📈 MÉTRICAS IMPORTANTES

Todas las métricas están disponibles en Grafana (http://localhost:3000):
- CPU y memoria de workers
- Tasks ejecutadas por segundo
- Duración promedio de tasks
- Métricas de contenedores Docker

Si necesitas hacer consultas personalizadas, Prometheus está disponible en http://localhost:9090
