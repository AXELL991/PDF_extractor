<<<<<<< HEAD
# 📄 pdf-extractext

Herramienta diseñada en Python para extraer texto de documentos PDF proporcionados por el usuario y generar un resumen automatizado utilizando un modelo de Inteligencia Artificial.

## 🚀 Tecnologías

* **Lenguaje:** Python (>=3.11)
* **Gestor de paquetes y entorno:** UV
* **Extracción PDF:** `pypdf`
* **Modelo de IA:** A definir (Soporte planeado para API REST o local mediante Ollama).
* **Base de datos:** MongoDB (NoSQL) para persistencia de los resúmenes.

## 🧠 Metodologías de Desarrollo

Este proyecto se rige por altos estándares de desarrollo de software:

* **TDD (Test-Driven Development):** El código se escribe priorizando las pruebas.
* **12 Factor App:** Aplicamos estrictamente los primeros 6 principios (Destacando: configuración almacenada en el entorno, dependencias explícitas, y código base único).
* **GitHub Flow:** Desarrollo dirigido a través de repositorios, ramas y Pull Requests.
* **Principios de Diseño:**
  * **SOLID:** Arquitectura orientada a interfaces e inyección de dependencias.
  * **KISS & YAGNI:** Mantenemos el código simple e iterativo. No añadimos funcionalidades hasta que son estrictamente necesarias.
  * **DRY:** Cero duplicación de lógica.

## 🛠️ Instalación y Uso Local

1. **Clonar el repositorio**
   ```bash
   git clone [https://github.com/TU_USUARIO/pdf-extractext.git](https://github.com/TU_USUARIO/pdf-extractext.git)
   cd pdf-extractext
=======
# pdf-extractext

Aplicación en Python para extraer texto de archivos PDF y generar resúmenes automáticos utilizando modelos de inteligencia artificial.

---

## Descripción

Este proyecto permite procesar documentos PDF de forma automatizada, extrayendo su contenido textual y generando resúmenes concisos mediante IA. Está diseñado con una arquitectura modular que facilita la escalabilidad, el mantenimiento y la integración de nuevos modelos o funcionalidades.

---

## Características
- Extracción de texto desde archivos PDF  
- Generación automática de resúmenes  
- Procesamiento eficiente de documentos  
- Arquitectura modular y extensible  
- Preparado para integrar múltiples modelos de IA  
- Persistencia de datos con MongoDB  
- Base lista para construir API o interfaz web  

---

## Tecnologías
- **Python**  
- **uv** (gestión de dependencias)  
- **MongoDB** (base de datos NoSQL)  
- **Modelo de IA** (a definir)  
- **Ollama** (integración opcional a futuro)  

---

## Instalación

```bash
git clone https://github.com/tu-usuario/pdf-extractext.git
cd pdf-extractext
uv sync
>>>>>>> 5926c66fcafb443573d4f07f9c8cef4ce85e89c6
