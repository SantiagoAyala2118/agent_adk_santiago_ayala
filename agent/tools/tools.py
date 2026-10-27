import json
from collections import Counter
from pathlib import Path

import requests

OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"
RUTA_LISTA = Path(__file__).resolve().parent.parent / "data" / "lista_lectura.json"
ACCIONES_VALIDAS = ["agregar", "quitar", "marcar_leido", "listar"]


def _cargar_lista() -> list:
    """Lee la lista de lectura desde el archivo JSON. Si no existe, devuelve una lista vacia."""
    if not RUTA_LISTA.exists():
        return []
    with open(RUTA_LISTA, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    if not isinstance(datos, list):
        raise ValueError("El archivo de la lista de lectura tiene un formato invalido.")
    return datos


def _guardar_lista(lista: list) -> None:
    """Guarda la lista de lectura en el archivo JSON."""
    RUTA_LISTA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_LISTA, "w", encoding="utf-8") as archivo:
        json.dump(lista, archivo, ensure_ascii=False, indent=2)


def _buscar_en_lista(lista: list, titulo: str):
    """Busca un libro en la lista por titulo (sin distinguir mayusculas)."""
    titulo_normalizado = titulo.strip().lower()
    for libro in lista:
        if libro["titulo"].lower() == titulo_normalizado:
            return libro
    return None


def buscar_libro(consulta: str, max_resultados: int = 5) -> dict:
    """
    Herramienta para buscar libros en el catalogo publico de Open Library.
    Utilizala cuando el usuario quiera encontrar un libro, conocer sus datos
    (autor, anio de publicacion, cantidad de paginas) o pida recomendaciones
    de libros de un autor o tema.
    Args:
        consulta: str -> Titulo, autor o tema a buscar.
        max_resultados: int -> Cantidad maxima de resultados (entre 1 y 10).
    """
    if not isinstance(consulta, str) or len(consulta.strip()) < 2:
        return {"status": "error", "mensaje": "La consulta debe ser un texto de al menos 2 caracteres."}
    if not isinstance(max_resultados, int) or not 1 <= max_resultados <= 10:
        return {"status": "error", "mensaje": "max_resultados debe ser un numero entero entre 1 y 10."}

    try:
        respuesta = requests.get(
            OPEN_LIBRARY_URL,
            params={
                "q": consulta.strip(),
                "limit": max_resultados,
                "fields": "key,title,author_name,first_publish_year,number_of_pages_median",
            },
            timeout=10,
        )
        respuesta.raise_for_status()
        documentos = respuesta.json().get("docs", [])
    except requests.exceptions.Timeout:
        return {"status": "error", "mensaje": "Open Library tardo demasiado en responder. Intenta nuevamente."}
    except requests.exceptions.RequestException as e:
        print("Error interno al utilizar la herramienta", e)
        return {"status": "error", "mensaje": f"No se pudo conectar con Open Library: {e}"}
    except ValueError:
        return {"status": "error", "mensaje": "Open Library devolvio una respuesta invalida."}

    if not documentos:
        return {"status": "vacio", "mensaje": f"No se encontraron libros para '{consulta}'."}

    libros = [
        {
            "titulo": doc.get("title", "Sin titulo"),
            "autores": doc.get("author_name", ["Autor desconocido"]),
            "anio_publicacion": doc.get("first_publish_year"),
            "paginas": doc.get("number_of_pages_median"),
            "enlace": f"https://openlibrary.org{doc['key']}" if doc.get("key") else None,
        }
        for doc in documentos
    ]
    return {"status": "ok", "cantidad": len(libros), "libros": libros}


def gestionar_lista_lectura(accion: str, titulo: str = "", autor: str = "", paginas: int = 0) -> dict:
    """
    Herramienta para administrar la lista de lectura personal del usuario.
    Utilizala cuando el usuario quiera agregar un libro a su lista, quitarlo,
    marcarlo como leido o ver los libros que tiene guardados.
    Args:
        accion: str -> Una de: "agregar", "quitar", "marcar_leido", "listar".
        titulo: str -> Titulo del libro. Obligatorio salvo para "listar".
        autor: str -> Autor del libro. Se usa solo al "agregar".
        paginas: int -> Cantidad de paginas del libro. Se usa solo al "agregar" (0 si se desconoce).
    """
    accion = accion.strip().lower() if isinstance(accion, str) else ""
    if accion not in ACCIONES_VALIDAS:
        return {"status": "error", "mensaje": f"Accion invalida. Las acciones validas son: {', '.join(ACCIONES_VALIDAS)}."}
    if accion != "listar" and (not isinstance(titulo, str) or not titulo.strip()):
        return {"status": "error", "mensaje": f"Para la accion '{accion}' es obligatorio indicar el titulo del libro."}
    if not isinstance(paginas, int) or paginas < 0:
        return {"status": "error", "mensaje": "La cantidad de paginas debe ser un numero entero mayor o igual a 0."}

    try:
        lista = _cargar_lista()

        if accion == "listar":
            if not lista:
                return {"status": "vacio", "mensaje": "La lista de lectura esta vacia."}
            return {"status": "ok", "cantidad": len(lista), "libros": lista}

        libro = _buscar_en_lista(lista, titulo)

        if accion == "agregar":
            if libro:
                return {"status": "error", "mensaje": f"'{libro['titulo']}' ya esta en la lista de lectura."}
            nuevo = {
                "titulo": titulo.strip(),
                "autor": autor.strip() if isinstance(autor, str) and autor.strip() else "Autor desconocido",
                "paginas": paginas,
                "leido": False,
            }
            lista.append(nuevo)
            _guardar_lista(lista)
            return {"status": "ok", "mensaje": f"'{nuevo['titulo']}' se agrego a la lista de lectura.", "libro": nuevo}

        if not libro:
            return {"status": "vacio", "mensaje": f"'{titulo}' no esta en la lista de lectura."}

        if accion == "quitar":
            lista.remove(libro)
            _guardar_lista(lista)
            return {"status": "ok", "mensaje": f"'{libro['titulo']}' se quito de la lista de lectura."}

        if libro["leido"]:
            return {"status": "ok", "mensaje": f"'{libro['titulo']}' ya estaba marcado como leido."}
        libro["leido"] = True
        _guardar_lista(lista)
        return {"status": "ok", "mensaje": f"'{libro['titulo']}' se marco como leido.", "libro": libro}

    except (OSError, ValueError) as e:
        print("Error interno al utilizar la herramienta", e)
        return {"status": "error", "mensaje": f"No se pudo acceder a la lista de lectura: {e}"}


def estadisticas_lectura() -> dict:
    """
    Herramienta para calcular estadisticas de la lista de lectura del usuario:
    total de libros, leidos, pendientes, porcentaje de avance, paginas leidas
    y autores mas frecuentes. Utilizala cuando el usuario pregunte por su
    progreso o un resumen de sus lecturas.
    """
    try:
        lista = _cargar_lista()
    except (OSError, ValueError) as e:
        print("Error interno al utilizar la herramienta", e)
        return {"status": "error", "mensaje": f"No se pudo acceder a la lista de lectura: {e}"}

    if not lista:
        return {"status": "vacio", "mensaje": "La lista de lectura esta vacia, no hay estadisticas para calcular."}

    leidos = [libro for libro in lista if libro.get("leido")]
    pendientes = [libro for libro in lista if not libro.get("leido")]
    autores = Counter(libro.get("autor", "Autor desconocido") for libro in lista)

    return {
        "status": "ok",
        "total_libros": len(lista),
        "leidos": len(leidos),
        "pendientes": len(pendientes),
        "porcentaje_leido": round(len(leidos) * 100 / len(lista), 1),
        "paginas_leidas": sum(libro.get("paginas", 0) for libro in leidos),
        "autores_mas_frecuentes": [
            {"autor": autor, "libros": cantidad} for autor, cantidad in autores.most_common(3)
        ],
        "titulos_pendientes": [libro["titulo"] for libro in pendientes],
    }
