<div align="center">

# 🔥 YT Outlier Lab

### Herramienta profesional de análisis de outliers y descubrimiento de oportunidades en YouTube

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-blue.svg)](https://mariadb.com/bsl11/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.14+-3F4F75?logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Status](https://img.shields.io/badge/Status-Active-success)]()

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Estructura](#-estructura-del-proyecto) • [Licencia](#-licencia)

</div>

---

## 📖 Descripción

**YT Outlier Lab** es una herramienta de análisis de datos de YouTube diseñada para creadores de contenido, analistas y marketers que buscan identificar videos con rendimiento excepcional (outliers) y descubrir oportunidades de contenido basadas en datos reales.

La aplicación utiliza la **YouTube Data API v3** para recopilar datos de videos y canales, aplica algoritmos estadísticos para detectar anomalías de rendimiento, y presenta los resultados en un dashboard interactivo con filtros avanzados.

---

## ✨ Características

### 🔍 Descubrimiento Inteligente
- **Auto-descubrimiento de videos** por categoría, región, idioma y palabras clave
- **Descubrimiento de canales** con filtros avanzados (suscriptores, videos, views totales)
- **Exploración de base de datos local** con los mismos filtros que la búsqueda API
- **Filtrado estricto por idioma** con validación en 3 capas (langdetect, scripts únicos, heurísticas)

### 📊 Análisis de Outliers
- **Cálculo de Outlier Score** con fórmula logarítmica: `log2(views / mediana_canal)`
- **Baseline robusto** usando mediana de los últimos 30 videos del canal
- **Exclusión del video actual** del baseline para mayor precisión
- **Métricas complementarias**: Views/hora, Views/suscriptor, edad del video

### 🎯 Filtros Avanzados
| Filtro | Opciones |
|---|---|
| 🎯 Categoría/Nicho | 15 categorías de YouTube |
| 🗣️ Idioma | Español, Inglés, Portugués, Francés, Alemán, Italiano |
| 🌍 País | 50+ regiones |
| 👁️ Views mínimas | 1K a 5M+ |
| 👥 Suscriptores máximos | 1K a 10M |
| ⏱️ Duración | Shorts, Cortos, Medios, Largos |
| 📈 Score mínimo | 0x a 6x |

### ⭐ Gestión de Contenido
- **Sistema de favoritos** con persistencia local
- **Análisis de outliers por canal** bajo demanda
- **Descarga automática de videos** de canales descubiertos
- **Persistencia en SQLite** para análisis offline

### 📈 Visualización
- **Scatter plot** Score vs Views (escala logarítmica)
- **Histograma** de distribución de scores
- **Cards interactivas** con thumbnails y métricas
- **Toast notifications** para feedback en tiempo real

---

## 🖼️ Screenshots

> 📸 *Próximamente: capturas del dashboard, sección de outliers y modal de análisis por canal.*

---

## 🛠️ Tecnologías

| Componente | Tecnología |
|---|---|
| **Backend** | Python 3.11+ |
| **Frontend** | Dash + Dash Bootstrap Components |
| **Visualización** | Plotly |
| **Base de datos** | SQLite + SQLAlchemy |
| **Machine Learning** | scikit-learn (clustering de temas) |
| **API** | YouTube Data API v3 |
| **Detección de idioma** | langdetect |
| **Procesamiento de imágenes** | Pillow |

---

## 📥 Instalación

### Requisitos previos

- **Windows 10/11**
- **Python 3.11 o superior** ([descargar](https://www.python.org/downloads/))
- **API Key de YouTube Data API v3** ([obtener aquí](https://console.cloud.google.com/apis/credentials))

### Opción 1: Desde el código fuente

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/yt-outlier-lab.git
cd yt-outlier-lab

# 2. Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key
copy .env.example .env
# Editar .env y agregar tu YOUTUBE_API_KEY

# 5. Ejecutar
python run.py
