# Celery en Kubernetes: La Guía Completa

## 📋 Tabla de Contenidos

- [Módulo 1: La Anatomía Real](#módulo-1-la-anatomía-real-lo-que-nadie-explica)
  - [El Mito del "Worker"](#1-el-mito-del-worker)
  - [El Problema de los Mega Pods](#el-problema-de-los-mega-pods)
  - [El Prefetching](#2-el-prefetching-el-asesino-silencioso-de-performance)
- [Módulo 2: Gestión de Recursos y Memoria](#módulo-2-gestión-de-recursos-y-memoria)
  - [La solución Nuclear: max_tasks_per_child](#1-la-solución-nuclear-max_tasks_per_child)
  - [La solución por Límite: max_memory_per_child](#2-la-solución-por-límite-max_memory_per_child)
- [Módulo 3: Tipos de Pools](#módulo-3-tipos-de-pools-la-clave-de-la-optimización)
  - [Comparación de Tipos de Pool](#comparación-de-tipos-de-pool)
  - [Tu optimización en K8s](#tu-optimización-en-k8s)
- [Módulo 4: Estrategia de Diseño en Kubernetes](#módulo-4-estrategia-de-diseño-en-kubernetes)
  - [Patrón 1: Split de Colas](#patrón-1-split-de-colas-obligatorio)
  - [Patrón 2: Fair Dispatch](#patrón-2-fair-dispatch-distribución-justa)
- [Resumen de Configuración Optimizada](#resumen-de-configuración-optimizada)

---

## Módulo 1: La Anatomía Real (Lo que nadie explica)

Celery no es solo "enviar tareas". Es un **sistema de tuberías**. Si una tubería es ancha y la otra angosta, todo explota.

### 1. El Mito del "Worker"

Cuando dices `celery worker`, no lanzas un proceso. Lanzas un **Supervisor** que a su vez lanza un **[Pool de Ejecución](pool_connections.md)**.

### El Problema de los Mega Pods

Si en Kubernetes le das a un Pod 10 CPUs y no configuras nada, Celery por defecto usa el modo **prefork** y lanza **10 sub-procesos Python independientes**.

**Consecuencia:** Cada proceso carga en RAM toda tu aplicación (Django/FastAPI + librerías).

> ⚠️ **Resultado:** Si tu app pesa 200MB en RAM, ese Pod consume:
> 
> $$200 \text{ MB} \times 10 = 2 \text{ GB}$$
> 
> Solo por arrancar, sin procesar nada.

---

### 2. El Prefetching (El asesino silencioso de performance)

Por defecto, Celery es "egoísta". Un worker intenta agarrar **4 tareas por adelantado** (multiplicado por el número de procesos).

#### Escenario Problemático

Tienes **2 workers**. Lanzas **1 tarea pesada** (10 min) y **100 tareas livianas** (1 seg).

**Problema:** El Worker A agarra la pesada... ¡y se reserva otras 3 livianas para después! Esas 3 tareas livianas se quedan bloqueadas en la memoria del Worker A esperando a que termine la pesada, mientras el Worker B está libre y muerto de risa.

> 🚨 **Síntoma en K8s:** Ves un pod al 100% CPU y otros al 0%, pero la cola no avanza.

---

## Módulo 2: Gestión de Recursos y Memoria 

Python no libera la memoria al sistema operativo inmediatamente (fragmentación). En procesos de larga duración como Celery, esto parece un "Memory Leak", pero es comportamiento normal de Python.

### 1. La solución Nuclear: `max_tasks_per_child`

Nunca confíes en que el **[Garbage Collector](garbage_collector.md)** de Python sea perfecto.

**Concepto:** Le dices al worker: "Procesa 1000 tareas y luego muérete".

**Efecto:** El proceso principal (Supervisor) mata al sub-proceso viejo y crea uno nuevo, limpio, con 0 RAM extra.

**Config:**

```bash
--max-tasks-per-child=1000
```

O menos si tienes leaks muy agresivos.

### 2. La solución por Límite: `max_memory_per_child`

Más segura para K8s. Si un worker supera X cantidad de RAM, se reinicia automáticamente.

**Uso:** Evita que el OOMKiller de Kubernetes mate todo el Pod. Es preferible que Celery reinicie un sub-proceso controladamente a que K8s mate el pod entero bruscamente.

---

## Módulo 3: Tipos de Pools (La clave de la optimización)

Aquí es donde optimizas "Mega Pods". Tienes que elegir el pool según tu tarea.

### Comparación de Tipos de Pool

| Tipo de Pool | Cómo funciona | Úsalo para... | No lo uses para... |
|--------------|---------------|---------------|---------------------|
| **Prefork** (Default) | 1 Proceso por Tarea | Cálculo pesado (CPU bound), Procesamiento de imágenes, Pandas/Numpy. | Peticiones HTTP, I/O, esperar bases de datos. |
| **Gevent / Eventlet** | Green Threads (Miles por proceso) | Network I/O, Web Scraping, llamar APIs externas, enviar emails. | Cálculos matemáticos (bloquean todo el pool). |

### Tu optimización en K8s

**Si tus tareas son llamar a APIs externas o esperar DB:**

- ❌ **NO** uses Prefork
- ✅ Usa **gevent**
- 💡 Podrás manejar **1000 tareas concurrentes** con 1 sola CPU y poca RAM

**Si tus tareas son CPU intensivas:**

- ✅ Usa **Prefork**, pero no hagas Mega Pods
- 💡 Haz muchos pods **pequeños** (1-2 CPUs)
- 📈 Es más fácil para el Autoscaler de K8s escalar 50 pods pequeños que 1 pod gigante

---

## Módulo 4: Estrategia de Diseño en Kubernetes

No trates a Celery como una caja negra. Divídelo.

### Patrón 1: Split de Colas (Obligatorio)

Nunca mezcles tareas rápidas con tareas lentas en la misma cola/worker.

- **Queue `default`:** Tareas rápidas (emails, notificaciones)
- **Queue `heavy`:** Reportes, procesamiento de video

#### En Kubernetes, tendrías Deployments separados:

- **`deployment-worker-default`:** Escala por CPU o número de mensajes
- **`deployment-worker-heavy`:** Escala diferente, quizás con nodos Spot de AWS

### Patrón 2: Fair Dispatch (Distribución Justa)

Para arreglar el problema de carga desbalanceada:

**`task_acks_late = True`:** La tarea solo se borra de RabbitMQ cuando termina. Si el worker muere a la mitad, RabbitMQ la reenvía a otro.

**`worker_prefetch_multiplier = 1`:** El worker nunca reserva tareas. Toma 1, la termina, y va por la siguiente.

> 📝 **Nota:** Esto baja un poco el rendimiento (más viajes a RabbitMQ) pero garantiza que ninguna tarea se quede "secuestrada" en un worker lento.

---

## Resumen de Configuración Optimizada

Para tu próximo despliegue (primero Docker Compose, luego K8s), esta es tu "Biblia de Configuración":

```python
# celeryconfig.py

# 1. Evitar que tareas largas bloqueen tareas cortas (Fair Dispatch)
task_acks_late = True
worker_prefetch_multiplier = 1 

# 2. Controlar Memoria (Anti-Leaks)
worker_max_tasks_per_child = 500  # Reiniciar proceso cada 500 tareas
worker_max_memory_per_child = 150000  # Reiniciar si usa más de 150MB (ajustar a tu pod)

# 3. Timeouts (Para que no se queden colgadas forever)
task_time_limit = 1800       # Kill -9 a los 30 min
task_soft_time_limit = 1500  # Exception a los 25 min (da tiempo a limpiar)

# 4. Serialización (Seguridad y peso)
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
```
