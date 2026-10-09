# Guía de contribución

¡Gracias por tu interés en mejorar el **Firmador de PDFs en Lote**! Este documento te ayudará a reportar problemas, proponer mejoras y enviar código de forma ordenada.

---

## 📋 Antes de empezar

- Revisa los [issues existentes](../../issues) para evitar duplicados.
- Si vas a proponer un cambio grande, abre primero un issue para discutirlo.
- Sé respetuoso y paciente con los demás colaboradores.

---

## 🐛 Reportar un bug

Usa la plantilla de reporte de bug y asegúrate de incluir:

1. **Descripción clara** del problema.
2. **Pasos para reproducirlo** (numerados).
3. **Comportamiento esperado** vs. **comportamiento real**.
4. **Entorno**:
   - Sistema operativo (Windows 11, macOS 14, Ubuntu 22.04, etc.)
   - Versión de Python (`python --version`)
   - Versión del proyecto (ver `CHANGELOG.md`)
5. **Capturas o logs** si aplica.

Un buen reporte permite reproducir el bug rápidamente. Un reporte vago suele quedar sin atender.

---

## 💡 Proponer una mejora

1. Abre un issue describiendo la propuesta con el título `[FEATURE] ...`.
2. Explica **qué problema resuelve** y **por qué sería útil**.
3. Menciona alternativas que hayas considerado.
4. Espera retroalimentación antes de invertir tiempo en implementarla.

---

## 🚀 Enviar código

### 1. Fork y clonar

```bash
# Haz fork desde GitHub, luego:
git clone https://github.com/Webnano/firmador-pdf.git
cd firmador-pdf