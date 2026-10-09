# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue las convenciones de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.2.0] — 2026-10-08

### Añadido
- **Vista previa con PDF real**: se puede seleccionar un PDF de la carpeta como fondo del preview, en lugar de la hoja simulada.
- **Selección individual de archivos**: ventana con checkboxes para elegir qué PDFs procesar (con scroll, botones "Todos", "Ninguno" e "Invertir").
- **Modo oscuro** activable desde el menú Ver o con `Ctrl+D`.
- **Tooltips** explicativos en todos los controles principales.
- **Botón Cancelar** para interrumpir un lote en curso sin cerrar la app.
- **Registro de actividad** en ventana aparte (`F2`), con el detalle de cada PDF procesado.
- **Manejo de PDFs protegidos con contraseña**: se detectan y se omiten sin romper el proceso.
- **Atajos de teclado** completos para todas las acciones principales.
- **Barra de menú** con secciones Archivo, Ver y Ayuda.
- **Instalación de dependencias** documentada en `requirements.txt`.

### Cambiado
- **Botones reorganizados en una sola fila**: Procesar, Cancelar y Registro conviven junto a "Elegir archivos" para no pelear con el tamaño de pantalla.
- **Ventana redimensionable** con tamaño inicial de 880×700 (cabe en pantallas de notebook).
- **Vista previa expandible**: ocupa todo el espacio vertical disponible.
- **`import fitz`** migrado a `import pymupdf as fitz` para evitar el warning de deprecación.

### Corregido
- La vista previa ya no se corta al achicar la ventana.
- El botón Procesar ya no queda fuera de la pantalla en monitores de notebook.

---

## [0.1.0] — 2026-10-07

### Añadido
- Versión inicial del Firmador de PDFs en Lote.
- Procesamiento por lote de todos los PDFs de una carpeta.
- Vista previa con página simulada.
- Posición base configurable (inferior/superior × izquierda/derecha + centro).
- Ajustes finos de posición con sliders (horizontal y vertical en % de la página).
- Arrastrar y soltar la firma con el mouse sobre la vista previa.
- Rotación de firma (±15°).
- Opacidad ajustable (10%–100%).
- Control del ancho de la firma (% del ancho de la página).
- Selector de páginas: todas, solo primera, solo última.
- Guardar y cargar configuración en JSON.
- Sin modificación de los PDFs originales (todo se guarda en carpeta de salida).

---

## Formato de versiones

- **MAJOR** (`X.0.0`): cambios incompatibles con versiones anteriores.
- **MINOR** (`0.X.0`): nuevas funcionalidades compatibles con versiones anteriores.
- **PATCH** (`0.0.X`): correcciones de errores compatibles con versiones anteriores.

## Tipos de cambios

- `Añadido` para nuevas funcionalidades.
- `Cambiado` para cambios en funcionalidades existentes.
- `Obsoleto` para funcionalidades que se eliminarán pronto.
- `Eliminado` para funcionalidades eliminadas.
- `Corregido` para corrección de errores.
- `Seguridad` para vulnerabilidades.

---

[0.2.0]: https://github.com/Webnano/firmador-pdf/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Webnano/firmador-pdf/releases/tag/v0.1.0