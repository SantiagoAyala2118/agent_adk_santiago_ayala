# agent_adk_santiago_ayala

Agente de inteligencia artificial desarrollado con **Python** y **Google Agent Development Kit (ADK)** que funciona como un **asistente de lectura**: busca libros en el catálogo público de [Open Library](https://openlibrary.org) y administra una lista de lectura personal, informando además estadísticas de progreso.

El agente no responde desde su propio conocimiento: interpreta la solicitud del usuario, decide qué herramienta (o combinación de herramientas) necesita, la ejecuta y construye la respuesta a partir de los resultados obtenidos.

## Componentes del agente

| Componente | Implementación |
|---|---|
| Modelo de IA | `gemma4:31b-cloud` servido por **Ollama** y conectado a ADK mediante **LiteLLM** (`LiteLlm("ollama_chat/gemma4:31b-cloud")`) |
| Instrucciones | Rol, objetivo, herramientas, comportamiento esperado y restricciones definidos en `agent/agent.py` |
| Herramientas | 3 herramientas con responsabilidades diferentes, en `agent/tools/tools.py` |
| Estado / memoria | La lista de lectura se persiste en `agent/data/lista_lectura.json` (se crea automáticamente) |
| Interfaz de prueba | Interfaz web de ADK (`adk web`) |

## Herramientas

### 1. `buscar_libro(consulta, max_resultados=5)`
Consulta la API de búsqueda de Open Library por título, autor o tema y devuelve título, autores, año de primera publicación, cantidad de páginas y enlace de cada libro.

- **Validaciones:** la consulta debe tener al menos 2 caracteres y `max_resultados` debe ser un entero entre 1 y 10.
- **Errores contemplados:** tiempo de espera agotado, falta de conexión, errores HTTP y respuestas inválidas de la API.
- **Resultado vacío:** si no hay coincidencias devuelve `status: "vacio"`.

### 2. `gestionar_lista_lectura(accion, titulo="", autor="", paginas=0)`
Administra la lista de lectura personal. Acciones disponibles:

| Acción | Descripción |
|---|---|
| `agregar` | Agrega un libro (no permite duplicados) |
| `quitar` | Quita un libro de la lista |
| `marcar_leido` | Marca un libro como leído |
| `listar` | Muestra todos los libros guardados |

- **Validaciones:** acción válida, título obligatorio (salvo en `listar`), páginas como entero mayor o igual a 0, títulos comparados sin distinguir mayúsculas.
- **Errores contemplados:** libro duplicado, archivo JSON dañado o inaccesible.
- **Resultado vacío:** lista vacía o libro inexistente devuelven `status: "vacio"`.

### 3. `estadisticas_lectura()`
Calcula un resumen de la lista: total de libros, leídos, pendientes, porcentaje de avance, páginas leídas, autores más frecuentes y títulos pendientes.

- **Errores contemplados:** archivo JSON dañado o inaccesible.
- **Resultado vacío:** si la lista no tiene libros devuelve `status: "vacio"`.

Todas las herramientas devuelven un diccionario con un campo `status` (`"ok"`, `"vacio"` o `"error"`) y un `mensaje` descriptivo, de modo que el agente siempre pueda explicarle al usuario qué ocurrió.

## Estructura del proyecto

```
agent_adk_santiago_ayala/
├── agent/
│   ├── __init__.py
│   ├── agent.py          # Definición del agente (modelo, instrucciones y herramientas)
│   ├── tools/
│   │   └── tools.py      # Implementación de las herramientas
│   ├── data/             # Se crea al usar el agente (lista_lectura.json)
│   ├── .env
│   └── .gitignore
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10 o superior
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) con el modelo `gemma4:31b-cloud` disponible
- Conexión a internet (para consultar Open Library)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd agent_adk_santiago_ayala
   ```
2. Crear y activar el entorno virtual:
   ```bash
   uv venv env && env\Scripts\activate   # En Windows
   uv venv env && source env/bin/activate # En Linux
   ```
3. Instalar las dependencias:
   ```bash
   uv pip install -r requirements.txt
   ```
4. Comprobar que Ollama está activo y que el modelo está disponible:
   ```bash
   ollama ls
   ```

## Uso

Desde la raíz del proyecto, ejecutar:

```bash
adk web
```

Luego abrir `http://localhost:8000` en el navegador, seleccionar el agente `agent` y comenzar a conversar.

### Ejemplos de solicitudes

| Solicitud | Herramientas que utiliza el agente |
|---|---|
| "Buscá libros de Isaac Asimov" | `buscar_libro` |
| "Agregá Fundación de Asimov a mi lista" | `buscar_libro` → `gestionar_lista_lectura` (agregar) |
| "Marcá Fundación como leído" | `gestionar_lista_lectura` (marcar_leido) |
| "¿Qué libros tengo en mi lista?" | `gestionar_lista_lectura` (listar) |
| "¿Cómo viene mi progreso de lectura?" | `estadisticas_lectura` |
| "Quitá El Principito de mi lista" (si no está) | `gestionar_lista_lectura` → informa resultado vacío |
| "¿Cuál es la capital de Francia?" | Ninguna: el agente indica que solo ayuda con libros y lectura |

## Autor

Santiago Tomás Ayala
