# Garbage Collector en Python

## 📋 Tabla de Contenidos

- [Concepto Clave: Liberación Automática de Memoria](#-concepto-clave-liberación-automática-de-memoria)
- [Mecanismos del Garbage Collector](#️-mecanismos-del-garbage-collector-en-python)
  - [Conteo de Referencias](#1-conteo-de-referencias-reference-counting)
  - [Recolector de Ciclos](#2-recolector-de-ciclos-generational-garbage-collector)
- [Garbage Collector en Celery](#-garbage-collector-en-celery)

---

## 🗑️ Concepto Clave: Liberación Automática de Memoria

En lenguajes de programación como **C** o **C++**, el desarrollador es el responsable de asignar y liberar la memoria manualmente. Si no se hace correctamente, pueden ocurrir **fugas de memoria** (memory leaks).

Python, en cambio, utiliza el **Garbage Collector** para hacer esta tarea de forma automática, simplificando la vida del desarrollador y haciendo que el manejo de la memoria sea mucho más seguro.

---

## ⚙️ Mecanismos del Garbage Collector en Python

Python utiliza dos mecanismos principales para la recolección de basura:

### 1. Conteo de Referencias (Reference Counting)

Este es el mecanismo **primario** y más fundamental en Python.

#### ¿Cómo funciona?

Cada objeto en Python lleva la cuenta de cuántas referencias (variables, listas, diccionarios, etc.) apuntan a él. Este contador se llama el **"contador de referencias"**.

#### Aumento y Disminución

- **Aumento:** El contador aumenta cada vez que se crea una nueva referencia al objeto (ej: `b = a`)
- **Disminución:** El contador disminuye cada vez que una referencia al objeto es eliminada o sale del ámbito (ej: la variable local de una función termina)

#### Liberación

Cuando el contador de referencias de un objeto llega a **cero**, Python sabe que el objeto ya no es accesible y, por lo tanto, puede ser liberado inmediatamente de la memoria.

---

### 2. Recolector Cíclico de Basura (Generational Garbage Collector)

Aunque el conteo de referencias es muy eficiente, tiene un gran problema: **no puede manejar referencias circulares** (o ciclos de referencias).

#### ¿Qué es una Referencia Circular?

Es cuando dos o más objetos se refieren entre sí, haciendo que su contador de referencias nunca llegue a cero, incluso si ya no son accesibles desde el resto del programa.

**Ejemplo:** Un objeto `A` apunta a `B`, y el objeto `B` apunta a `A`.

#### La Solución

Aquí es donde entra el **recolector cíclico**. Este es un mecanismo opcional que se ejecuta periódicamente para identificar y limpiar estos ciclos de objetos inaccesibles.

Python lo implementa como un **recolector generacional**, lo que significa que divide los objetos en tres "generaciones" para optimizar el proceso:

- **Generación 0:** Objetos más nuevos. Se comprueba con más frecuencia
- **Generación 1:** Objetos que sobrevivieron a una recolección de Generación 0. Se comprueba menos a menudo
- **Generación 2:** Objetos que sobrevivieron a una recolección de Generación 1. Se comprueba la menor cantidad de veces

> 💡 **Optimización:** La idea es que la mayoría de los objetos son de corta duración, por lo que revisar solo la Generación 0 con frecuencia ahorra tiempo.

---

## 💡 Resumen de la Ventaja

El Garbage Collector en Python te asegura que no tienes que preocuparte por liberar la memoria explícitamente, lo que:

- ✅ Previene fugas de memoria por olvidos
- ✅ Simplifica el código y el desarrollo
- ✅ Mejora la seguridad del programa al gestionar la memoria de forma robusta

---

## 📜 Ejemplo de Ciclo de Referencias en Python

Imagina que tenemos dos clases, `A` y `B`, y hacemos que una instancia de `A` contenga una referencia a una instancia de `B`, y viceversa.

### Paso 1: Creación del Ciclo

```python
import sys

class ObjetoA:
    def __init__(self, nombre):
        self.nombre = nombre
        self.referencia_a_B = None # Inicialmente no apunta a nada

    def __del__(self):
        # Este método se llama cuando el objeto es DESTRUIDO por el GC
        print(f"--- Objeto A ({self.nombre}) DESTRUIDO ---")

class ObjetoB:
    def __init__(self, nombre):
        self.nombre = nombre
        self.referencia_a_A = None

    def __del__(self):
        print(f"--- Objeto B ({self.nombre}) DESTRUIDO ---")

# --- Creación de los objetos y el ciclo ---
def crear_ciclo():
    a = ObjetoA("Instancia A")
    b = ObjetoB("Instancia B")
    
    # 1. Creamos la referencia cruzada (el ciclo)
    a.referencia_a_B = b 
    b.referencia_a_A = a
    
    # 2. El contador de referencias de 'a' y 'b' es ahora > 1:
    #    - 'a' es referenciado por la variable local 'a' y por 'b.referencia_a_A'
    #    - 'b' es referenciado por la variable local 'b' y por 'a.referencia_a_B'
    
    print("Contadores de referencias después del ciclo (solo variables locales):")
    # Nota: sys.getrefcount() siempre reporta 1 más de lo real por su propia llamada
    print(f" Ref. de A: {sys.getrefcount(a)}") 
    print(f" Ref. de B: {sys.getrefcount(b)}")
    
    # Cuando esta función termina, las variables locales 'a' y 'b'
    # dejan de existir. ¡Pero los objetos *no* se destruyen!

# Ejecutamos la función. Verás que no aparece el mensaje "__del__"
print("--- 1. Llamando a crear_ciclo() ---")
crear_ciclo()
print("--- Fin de la función crear_ciclo(). Los objetos *deben* haber sido liberados, pero no lo están. ---")
print("---------------------------------------------------------------------------------------------------\n")
```

**Resultado de la Ejecución del Paso 1:** No ves los mensajes de `DESTRUIDO`. Esto confirma la fuga: los objetos ya no son accesibles desde fuera de la función, pero su contador de referencias cruzadas mantiene el valor mayor que cero, engañando al conteo de referencias.

### Paso 2: Ejecución Manual del Garbage Collector Cíclico

Ahora, forzaremos al recolector cíclico a ejecutarse para que detecte el ciclo de referencias que el conteo de referencias ignoró:

```python
import gc

# Forzamos al Recolector Cíclico a buscar y limpiar ciclos
print("--- 2. Ejecutando gc.collect() para limpiar el ciclo ---")
objetos_limpiados = gc.collect()
print(f"El GC limpió {objetos_limpiados} objetos. Debería ser 2 (A y B).\n")
print("---------------------------------------------------------------------------------------------------\n")
```

**Resultado de la Ejecución del Paso 2:**

```
--- Objeto A (Instancia A) DESTRUIDO ---
--- Objeto B (Instancia B) DESTRUIDO ---
El GC limpió 2 objetos. Debería ser 2 (A y B).
```

Ahora sí aparecen los mensajes `DESTRUIDO`, confirmando que el Garbage Collector cíclico identificó el ciclo inaccesible y liberó ambos objetos de la memoria.

### 📝 Resumen del Ejemplo

**Conteo de Referencias (Falla):** Cuando `crear_ciclo()` finalizó, las variables locales `a` y `b` se eliminaron. Sus contadores de referencias disminuyeron, pero no llegaron a cero porque las referencias cruzadas (`a.referencia_a_B` y `b.referencia_a_A`) los mantuvieron "vivos". El mecanismo principal falló en la limpieza.

**Recolector Cíclico (Actúa):** Al ejecutar `gc.collect()`, el mecanismo secundario inspeccionó la memoria, determinó que el conjunto de objetos `A` y `B` no era accesible desde ningún otro lugar del programa, y procedió a liberarlos.

> 🎯 Este es el rol vital que cumple el recolector cíclico en Python.

---

## 🔧 Garbage Collector en Celery

Celery es un sistema de gestión de tareas distribuido. Sus **workers** (trabajadores) son procesos de larga duración que están constantemente a la espera de ejecutar tareas (funciones de Python).

El Garbage Collector afecta a Celery de dos maneras principales: la **liberación de memoria después de cada tarea** y la **gestión de posibles fugas de memoria**.

### 1. ♻️ Liberación de Recursos Después de la Tarea

Celery ejecuta cada tarea como una unidad discreta. Cuando una tarea finaliza, todas las variables locales y objetos grandes creados dentro de esa tarea deberían ser liberados por el Garbage Collector de Python.

#### Impacto Positivo

El conteo de referencias (el mecanismo principal de GC) debería asegurar que la memoria consumida por los datos de la tarea se libere inmediatamente después de que la función termina, lo cual es ideal para un proceso de larga duración.

#### Problema de Fugas (Memory Leaks)

Si dentro de una tarea se crea un **ciclo de referencias** (donde los objetos se apuntan mutuamente), el conteo de referencias falla. En estos casos, el objeto permanece en la memoria hasta que el Recolector Cíclico de Basura de Python se ejecuta.

> ⚠️ **Riesgo:** Si un worker de Celery está ocupado ejecutando muchas tareas y creando ciclos de referencias, y el recolector cíclico no se ejecuta lo suficientemente rápido, la memoria del worker aumentará progresivamente (lo que se percibe como una fuga de memoria).

**Consecuencias:**

- Degradación del rendimiento del sistema operativo (por el uso de swap o memoria virtual)
- Que el sistema operativo (kernel) termine el proceso del worker si supera un límite (OOM Killer)

---

### 2. 🧱 Estrategias de Celery para Mitigar Fugas de Memoria

Debido a que las fugas causadas por ciclos de referencias son un problema común en cualquier proceso Python de larga duración (como los workers de Celery), Celery tiene mecanismos integrados para combatirlas:

#### A. Reinicio de Worker por Tarea (la Solución más Común)

Este es el mecanismo más efectivo de Celery para garantizar que la memoria se limpie por completo.

**`--max-tasks-per-child`:** Este es un parámetro fundamental. Permite especificar cuántas tareas debe ejecutar un proceso worker antes de que Celery lo finalice y lo reemplace por uno nuevo.

> 🔄 **Efecto en el GC:** Al matar el proceso (child process), el sistema operativo recupera toda la memoria asignada a ese proceso, lo que garantiza una limpieza total, incluso de posibles referencias circulares o fugas en bibliotecas de terceros que el GC de Python no pudo manejar.

#### B. Reinicio de Worker por Memoria

**`--max-memory-per-child`:** Celery (en versiones más recientes o a través de extensiones) puede configurarse para monitorear el consumo de memoria. Si un worker supera un límite predefinido (ej. 250MB), se reinicia tras completar su tarea actual, lo que también fuerza la liberación de memoria.

#### C. Control Manual del Garbage Collector

En tareas particularmente intensivas en memoria o de larga duración, a veces los desarrolladores fuerzan la ejecución del recolector cíclico usando el módulo `gc`:

```python
import gc
from celery import shared_task

@shared_task
def tarea_intensiva():
    # Código que consume mucha memoria y puede crear ciclos...
    resultado = procesar_datos_gigantes()
    # Forzar la recolección de basura después de que los objetos grandes
    # han salido del ámbito (o se ha usado `del`)
    gc.collect()
    return resultado
```

> ⚠️ **Advertencia:** Esto debe usarse con criterio, ya que la ejecución manual de `gc.collect()` puede introducir pausas (latency) en el worker mientras el GC está activo.

---

## 📝 Conclusión

El Garbage Collector de Python es el encargado de la limpieza de memoria en Celery, siendo el **conteo de referencias** el método más rápido y frecuente. Sin embargo, en un entorno de Celery (que utiliza procesos de larga duración), los **ciclos de referencias** pueden causar una acumulación de memoria que se resuelve con la limpieza periódica del recolector cíclico.

> 🎯 **Solución recomendada:** Para garantizar la estabilidad y evitar que los workers se queden sin memoria, la solución más común en Celery es la configuración de `--max-tasks-per-child` para que los procesos se reinicien regularmente.

---

## 👶 Concepto Clave: El Proceso Child (Hijo)

La configuración "per child" en Celery es la clave para manejar la memoria en procesos de larga duración. Vamos a explicarlo con un ejemplo concreto sobre cómo funciona el `--max-tasks-per-child` y por qué es una solución tan robusta contra las fugas de memoria, incluso si el Garbage Collector (GC) de Python no logra limpiar todos los ciclos de referencias.

En Celery, cuando inicias el worker, se crea un proceso principal (**Padre**), que a su vez lanza varios procesos de trabajo (**Hijos** o Children).

- El **Proceso Padre** es el supervisor
- Los **Procesos Hijos** son los que realmente ejecutan las tareas de Python

Celery se enfoca en gestionar la vida de estos procesos hijos.

---

## 🔨 Ejemplo Práctico: El Worker con Fuga de Memoria

Imagina que tienes un worker de Celery con 4 procesos hijos ejecutando una tarea de Python que, sin que te des cuenta, crea un pequeño ciclo de referencias en cada ejecución (una micro-fuga).

| Parámetro | Valor | Significado |
|-----------|-------|-------------|
| `--concurrency` | 4 | El worker tiene 4 procesos hijos ejecutando tareas. |
| `--max-tasks-per-child` | Sin definir (Infinito) | Un proceso hijo ejecuta tareas infinitas y nunca se reinicia. |
| Consumo de memoria | 100 MB | Memoria inicial de cada proceso hijo. |

### Escenario 1: Sin Límite (--max-tasks-per-child Deshabilitado)

El proceso **Hijo #1** ejecuta 1000 tareas. Cada tarea tiene una micro-fuga de 0.1 MB que el GC cíclico no detecta inmediatamente.

- **Consumo de Memoria del Hijo #1:** $100 \text{ MB} + (1000 \text{ tareas} \times 0.1 \text{ MB/tarea}) = 200 \text{ MB}$

- Después de 10,000 tareas, el Hijo #1 ha consumido: $100 \text{ MB} + (10000 \text{ tareas} \times 0.1 \text{ MB/tarea}) = 1100 \text{ MB}$ (1.1 GB)

- El proceso sigue ejecutando tareas, y su consumo de memoria **nunca se reinicia** y sigue creciendo hasta agotar la memoria disponible en el servidor (OOM Killer)

### Escenario 2: Con Límite (--max-tasks-per-child = 200)

Ahora configuramos el worker de esta manera:

```bash
celery -A your_app worker --loglevel=info --concurrency=4 --max-tasks-per-child=200
```

| Parámetro | Valor |
|-----------|-------|
| `--max-tasks-per-child` | 200 |

**Flujo de ejecución:**

1. **Hijo #1** ejecuta 199 tareas. Su consumo de memoria ha subido ligeramente a: $100 \text{ MB} + (199 \text{ tareas} \times 0.1 \text{ MB/tarea}) \approx 120 \text{ MB}$

2. Al empezar la **tarea número 200**, el proceso Padre se da cuenta de que el Hijo #1 alcanzó su límite

3. El proceso Padre **FINALIZA y MATA** al proceso Hijo #1

4. El sistema operativo (Linux, Windows, etc.) libera instantáneamente toda la memoria de **120 MB** que estaba usando el Hijo #1

5. El proceso Padre **CREA un proceso Hijo #5** nuevo y fresco

6. El Hijo #5 comienza a ejecutar la tarea 200 con su consumo de memoria base de **100 MB**

---

## 🔑 Por qué esto "Arregla" la Fuga

La clave es que, al matar el proceso completo, la limpieza de memoria ya no depende del Garbage Collector de Python.

- El **Garbage Collector de Python** limpia objetos **dentro** de un proceso
- **Matar el proceso** y dejar que el sistema operativo lo limpie es una limpieza **externa y total**

Al reiniciar los procesos hijos con frecuencia (cada 200 tareas en este ejemplo), se garantiza que cualquier fragmento de memoria que no pudo ser limpiado (ciclos de referencias, memoria de librerías C, etc.) sea liberado forzosamente antes de que crezca demasiado.

### Comparación de Estrategias

| Estrategia | Ventaja | Dependencia |
|------------|---------|-------------|
| `gc.collect()` (Interna) | Limpia objetos inmediatamente | Depende de que no haya ciclos de referencias o fugas en código C |
| `--max-tasks-per-child` (Externa) | Limpieza forzosa total y garantizada | No depende de la lógica del GC de Python; depende del sistema operativo |

> 💡 **Recomendación:** Se recomienda siempre usar un valor bajo (ej. 100 o 200) para `--max-tasks-per-child` en workers que ejecutan tareas complejas o intensivas en memoria.