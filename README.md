# 📝 Firmador de PDFs en Lote

Aplicación de escritorio para **insertar una firma (imagen PNG/JPG) en múltiples PDFs de forma automática**, con control visual preciso de posición, tamaño, rotación y opacidad. Incluye vista previa sobre el documento real, modo oscuro, selección individual de archivos y guardado de configuración.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Version](https://img.shields.io/badge/version-0.2.0-orange)

---

## ✨ Características

### 🖋️ Firma de PDFs
- 📁 **Procesamiento por lote**: firma todos los PDFs de una carpeta en una sola operación.
- 📄 **Selector de páginas**: firmar todas, solo la primera o solo la última.
- 🛡️ **No modifica los originales**: los PDFs firmados se guardan en una carpeta aparte.
- 🔒 **Detecta PDFs protegidos con contraseña** y los omite sin romper el proceso.

### 👁️ Vista previa avanzada
- 🖼️ **Fondo con el PDF real**: previsualiza la firma sobre el documento real, no sobre una hoja simulada.
- 🎯 **Posición base**: inferior/superior × izquierda/derecha + centro.
- 🖱️ **Arrastrar y soltar** la firma con el mouse directamente en la vista previa.
- 📐 **Sliders de ajuste fino** (horizontal y vertical) en % del tamaño de la página.
- 🔄 **Rotación de firma** (±15°) para un acabado más natural.
- 🔍 **Opacidad ajustable** (10%–100%).

### 🎨 Experiencia de usuario
- 🌙 **Modo oscuro** activable con `Ctrl+D`.
- ☑️ **Selección individual de archivos** (con checkboxes) para procesar solo los que quieras.
- 💾 **Guardar/cargar configuración** en JSON para no reconfigurar cada vez.
- 📋 **Registro de actividad** con el detalle de cada PDF procesado.
- ⏹️ **Botón Cancelar** para detener un lote en curso.
- 💬 **Tooltips** explicativos en todos los controles.
- ⌨️ **Atajos de teclado** completos.
- 🖱️ **Interfaz redimensionable** que se adapta al tamaño de la pantalla.

---

## 📸 Notas Autor

> _trabaja con carpetas separadas:

| PDFs_prueba | usala para tus PDFs Originales |

| PDFs_firmados | usala para tus PDFs Modificados |

---

## 🚀 Requisitos

- **Python 3.8 o superior**
- Sistemas operativos soportados: **Windows, macOS y Linux**
- `tkinter` viene incluido con Python (no requiere instalación aparte).

### Dependencias

| Paquete | Uso |
|---|---|
| [`PyMuPDF`](https://pymupdf.readthedocs.io/) (`fitz`) | Manipulación de PDFs y renderizado de la página de preview |
| [`Pillow`](https://python-pillow.org/) (`PIL`) | Apertura, rotación, redimensionado y opacidad de la firma |

---

## 📦 Instalación

1. **Clona el repositorio**:

   ```bash
   git clone https://github.com/Webnano/firmador-pdf.git
   cd firmador-pdf