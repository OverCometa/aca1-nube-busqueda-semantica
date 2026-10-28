# ACA 1 · Computación en la Nube

**Over Santiago Cometa Hernández · CUN · Trabajo individual**

Prototipo de ingesta, embeddings abiertos y búsqueda semántica Top-3 sobre tres guías didácticas de elaboración propia. La base vectorial está en Qdrant Cloud; el catálogo SQL local utiliza SQLite. No es un chatbot generativo ni un servicio institucional de CUN.

## Organización

- `notebook/ACA1_Computacion_Nube.ipynb`: desarrollo y salidas reales.
- `src/pipeline.py`: lectura, chunking, embeddings, carga y consultas remotas.
- `corpus/`: tres guías en Markdown y manifiesto de fuentes.
- `data/`: dataset UCI y consultas con temas esperados.
- `results/`: fragmentos, auditoría y validación.
- `poster/`: infografía PDF y su generador.

## Ejecutar

Python 3.12. Extraer o clonar el proyecto completo, ejecutar `pip install -r requirements.txt`, copiar `.env.example` a `.env` y configurar una URL y clave de Qdrant propias. No publicar `.env` ni capturar las claves en video. Abrir el notebook y ejecutar secuencialmente. Si falta el CSV, se descarga de UCI. El modelo abierto se descarga una vez y ejecuta en CPU. Se requiere conexión para consultar Qdrant.

El notebook crea la colección `aca1_permanencia_documental_v1` si no existe. La carga es idempotente para el mismo corpus. Al modificar documentos o modelo, versionar la colección. Nunca utiliza una base local como sustituto silencioso del clúster remoto.

## Alcance y evaluación

Datos UCI 697 de Portugal, separados de los documentos de orientación colombiana. La asociación es temática mediante campos del dataset; no se enlazan personas ni se demuestra causalidad. Los manuales son propuestas didácticas propias, no reglamentos oficiales.

Seis consultas predefinidas, Top-3 y puntuaciones coseno. Las métricas de coincidencia temática son exploratorias; no equivalen a juicios humanos de relevancia o exactitud general. Ver notebook para resultados, límites y referencias APA 7.

El clúster gratuito es gestionado y de un nodo; no se atribuye alta disponibilidad ni escalado serverless ilimitado. El video de sustentación debe grabarse con voz propia y durar 3-5 minutos. Su enlace se agregará al póster después de publicarlo.
