# Guía de demostración (máximo 15 minutos)

**Antes de empezar (5 minutos antes):**

1. Abra https://console.neo4j.io y compruebe que la instancia esté **Running**. Las instancias Free se pausan tras unos días sin uso; si está pausada, pulse *Resume* y espere 1-2 minutos.
2. En la terminal de VS Code ejecute `.venv\Scripts\activate` y después `streamlit run app.py`. Abra http://localhost:8501.
3. Tenga abierta una pestaña de **Neo4j Browser/Query** de la instancia (opcional, para mostrar el grafo "por dentro").
4. Si en ensayos anteriores modificó datos, ejecute `python scripts\inicializar_bd.py --actualizar` (o, con la cuenta de administrador, *Administración → Base de datos → Cargar / completar datos de demostración*) para restaurarlos. No borra nada.
5. Si la cuenta "Ana Demo" quedó de un ensayo, elimínela antes (Mi perfil → Seguridad) para poder registrarla en vivo.

| Min. | Sección | Qué hacer y qué decir |
|---|---|---|
| 0:00-1:30 | **Introducción** | Presente el problema (datos altamente interconectados) y por qué un grafo. Muestre el diagrama `docs/modelo_grafo.png`: 5 nodos y 8 relaciones, incluida `USA_TECNOLOGIA`. |
| 1:30-3:00 | **Registro e inicio de sesión** | *Crear cuenta* con "Ana Demo" / `ana.demo@ejemplo.com`: muestre primero los errores de validación (contraseña débil, correo inválido) y luego créela. Entra directo a *Mi perfil*: agregue Python (4), SQL (3) y Neo4j (3). En *Experiencia*, vincúlela a Cumbre Talento. |
| 3:00-4:00 | **Mi red e Inicio** | Desde *Mi red → Descubrir personas*, invite a Valentina Rojas. Cierre sesión, entre como `valentina.rojas@ejemplo.com` (`Demo2026*`) y acepte la invitación en *Inicio*. Muestre el panel personal: empleos con su porcentaje de compatibilidad y la fortaleza del perfil. |
| 4:00-5:45 | **Reclutador** | Entre como `daniela.vargas@ejemplo.com` (reclutadora de Andina Analytics). En *Mi empresa → Publicar oferta*, publique "Analista de Grafos" con Neo4j y Python obligatorias. En *Candidatos recomendados*, Ana Demo y David Cardona aparecen arriba. Muestre que **no puede** gestionar ofertas de otra empresa: el permiso se resuelve con el grafo. |
| 5:45-7:45 | **Rutas y conexiones** | *Contactos en común*: Valentina Rojas y Daniela Vargas (3). *Ruta más corta*: Julián Torres → CiberEscudo con "Red profesional" (4 saltos por personas), luego con "Cualquier relación" (la ruta cambia). Usuario → **Oferta**: Esteban Uribe → Arquitecto Cloud con "Todas las rutas mínimas" (8 rutas). Muestre que Sofía Cárdenas no tiene ruta a Andina Analytics (componente aislado). |
| 7:45-10:00 | **Recomendaciones** | *Candidatos*: oferta "Ingeniero de Grafos Neo4j": explique la fórmula 0,7·competencias + 0,3·red con Valentina (83 % de cobertura y un contacto dentro). *Empleos*: Elena Ríos (sin contactos: solo pesa la cobertura). *Contactos*: Julián Torres → Daniela Vargas (17 puntos) y pulse **Conectar**. *Habilidades similares*: pares con Jaccard 1,0. |
| 10:00-12:00 | **Analítica** | *Influyentes*: Alejandro Restrepo (mayor intermediación = puente entre comunidades). *Comunidades*: Louvain detecta 6 comunidades, modularidad 0,63, coloreadas en el grafo. Cambie a "Componentes conectados" (3) y explique la diferencia y las limitaciones. *Habilidades demandadas*: demanda frente a talento disponible. |
| 12:00-13:00 | **Proyectos y explorador** | *Proyectos relacionados*: Red Social Interna con Grafos ↔ Plataforma de Comercio Electrónico. *Explorador*: vecindario de 2 saltos de Ana Demo y vista por tipos. |
| 13:00-14:30 | **Investigación** | Compare la consulta de "contactos de 2.º grado en la empresa X con Python": 9 `JOIN` en SQL frente a 2 líneas en Cypher (sección 7 del documento). Cuándo gana el grafo y cuándo el relacional. |
| 14:30-15:00 | **Cierre** | Pruebas: 65/65 aprobadas contra AuraDB (`pytest`). Conclusión principal. Al final, como Ana Demo, use *Mi perfil → Seguridad → Eliminar mi cuenta* para mostrar `DETACH DELETE`. |

**Plan de contingencia:** si se pierde la conexión con AuraDB, muestre `docs/evidencias.md`, que contiene resultados reales generados con la base, y las capturas de pantalla que haya tomado durante el ensayo.
