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