# Evidencias de funcionamiento

Generado automáticamente por `scripts/generar_evidencias.py` el 2026-11-11 23:34 ejecutando las consultas **contra la instancia real de Neo4j AuraDB**.

**Servidor:** Neo4j Kernel 5.27-aura (enterprise)

## Contenido de la base

| Etiqueta | Nodos |
|---|---|
| Usuario | 43 |
| Empresa | 12 |
| Habilidad | 37 |
| Proyecto | 15 |
| Oferta | 22 |

| Relación | Total |
|---|---|
| TIENE_HABILIDAD | 194 |
| CONECTA_CON | 84 |
| REQUIERE | 81 |
| USA_TECNOLOGIA | 63 |
| PARTICIPA_EN | 55 |
| TRABAJA_EN | 50 |
| POSTULA_A | 25 |
| PUBLICA | 22 |

## Restricciones de unicidad

| name | labelsOrTypes | properties | type |
|---|---|---|---|
| empresa_id | Empresa | id | NODE_PROPERTY_UNIQUENESS |
| empresa_nombre | Empresa | nombre | NODE_PROPERTY_UNIQUENESS |
| habilidad_nombre | Habilidad | nombre | NODE_PROPERTY_UNIQUENESS |
| oferta_id | Oferta | id | NODE_PROPERTY_UNIQUENESS |
| proyecto_id | Proyecto | id | NODE_PROPERTY_UNIQUENESS |
| usuario_email | Usuario | email | NODE_PROPERTY_UNIQUENESS |
| usuario_id | Usuario | id | NODE_PROPERTY_UNIQUENESS |

## 1. ¿Qué usuarios tienen habilidades similares?

Similares a **Valentina Rojas** (Jaccard):

| nombre | compartidas | en_comun | jaccard | ya_conectados |
|---|---|---|---|---|
| Mariana López | Python, Machine Learning, Deep Learning, Inglés | 4 | 0.444 | False |
| Natalia Suárez | Python, Deep Learning, Estadística, Inglés | 4 | 0.444 | True |
| Elena Ríos | Python, SQL, Estadística | 3 | 0.333 | False |
| Laura Castillo | Python, SQL, Estadística | 3 | 0.333 | True |
| Juliana Escorcia | Python, SQL, Estadística | 3 | 0.3 | False |

Pares más similares de toda la red:

| usuario_a | usuario_b | compartidas | jaccard |
|---|---|---|---|
| Laura Castillo | Elena Ríos | Python, SQL, Estadística, Power BI | 1.0 |
| Andrés Caicedo | Jorge Escobar | Python, Linux, Ciberseguridad, Redes | 1.0 |
| Laura Castillo | Juliana Escorcia | Python, SQL, Estadística, Power BI | 0.8 |
| Juliana Escorcia | Elena Ríos | Python, SQL, Estadística, Power BI | 0.8 |
| Isabella Mejía | Luisa Echeverri | JavaScript, TypeScript, React, HTML/CSS | 0.8 |

## 2. ¿Qué contactos en común existen entre dos profesionales?

Entre **Valentina Rojas** y **Daniela Vargas**:

| nombre | titular | conexiones |
|---|---|---|
| Laura Castillo | Analista de Riesgo Cuantitativo | 6 |
| Sebastián Pardo | Ingeniero MLOps | 6 |
| Natalia Suárez | Investigadora en Inteligencia Artificial | 5 |

## 3. ¿Cuál es la ruta más corta entre un usuario y una empresa?

- **Julián Torres → CiberEscudo** (Red profesional (contactos y empleos)): 4 saltos: `Julián Torres -[CONECTA_CON]- Sebastián Pardo (Usuario) -[CONECTA_CON]- Carlos Mosquera (Usuario) -[CONECTA_CON]- Jorge Escobar (Usuario) -[TRABAJA_EN]- CiberEscudo (Empresa)`

- **Elena Ríos → Andina Analytics** (Cualquier relación del grafo): 3 saltos: `Elena Ríos -[TIENE_HABILIDAD]- Python (Habilidad) -[TIENE_HABILIDAD]- Valentina Rojas (Usuario) -[TRABAJA_EN]- Andina Analytics (Empresa)`

- **Sofía Cárdenas → Andina Analytics** (Red profesional (contactos y empleos)): sin ruta (componentes distintos)


Todas las rutas mínimas de **Esteban Uribe** a la oferta **Arquitecto Cloud** (8 rutas de 5 saltos):

1. `Esteban Uribe -[CONECTA_CON]- David Cardona (Usuario) -[CONECTA_CON]- Valentina Rojas (Usuario) -[CONECTA_CON]- Sebastián Pardo (Usuario) -[TRABAJA_EN]- Pacífico Cloud (Empresa) -[PUBLICA]- Arquitecto Cloud (Oferta)`

2. `Esteban Uribe -[CONECTA_CON]- Paula Montoya (Usuario) -[CONECTA_CON]- Alejandro Restrepo (Usuario) -[CONECTA_CON]- Diana Valencia (Usuario) -[TRABAJA_EN]- Pacífico Cloud (Empresa) -[PUBLICA]- Arquitecto Cloud (Oferta)`

3. `Esteban Uribe -[TRABAJA_EN]- Paisa Software (Empresa) -[TRABAJA_EN]- Alejandro Restrepo (Usuario) -[CONECTA_CON]- Diana Valencia (Usuario) -[TRABAJA_EN]- Pacífico Cloud (Empresa) -[PUBLICA]- Arquitecto Cloud (Oferta)`

4. `Esteban Uribe -[CONECTA_CON]- Mateo Giraldo (Usuario) -[CONECTA_CON]- Alejandro Restrepo (Usuario) -[CONECTA_CON]- Diana Valencia (Usuario) -[TRABAJA_EN]- Pacífico Cloud (Empresa) -[PUBLICA]- Arquitecto Cloud (Oferta)`

5. `Esteban Uribe -[CONECTA_CON]- David Cardona (Usuario) -[CONECTA_CON]- Alejandro Restrepo (Usuario) -[CONECTA_CON]- Diana Valencia (Usuario) -[TRABAJA_EN]- Pacífico Cloud (Empresa) -[PUBLICA]- Arquitecto Cloud (Oferta)`


## 4. ¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias?

Oferta **Ingeniero de Grafos Neo4j · Cumbre Talento**:

| nombre | puntaje | cobertura_pct | cumple | faltan | contactos_en_empresa | contactos_2do_grado | ya_postulado |
|---|---|---|---|---|---|---|---|
| Valentina Rojas | 68.3 | 83.3 | Python, SQL, Neo4j | Docker | Camila Herrera | 0 | False |
| David Cardona | 63.3 | 83.3 | Python, SQL, Neo4j | Docker |  | 1 | False |
| Santiago Morales | 45.0 | 50.0 | Python, Docker | SQL, Neo4j | Camila Herrera | 0 | False |
| Alejandro Restrepo | 40.0 | 50.0 | Neo4j, Docker | Python, SQL |  | 1 | True |
| Andrés Gómez | 40.0 | 50.0 | Python, SQL | Neo4j, Docker |  | 1 | True |
| Laura Castillo | 40.0 | 50.0 | Python, SQL | Neo4j, Docker |  | 1 | False |

Oferta **Científico de Datos Semi Senior · Andina Analytics**:

| nombre | puntaje | cobertura_pct | cumple | faltan | contactos_en_empresa | contactos_2do_grado | ya_postulado |
|---|---|---|---|---|---|---|---|
| Laura Castillo | 70.0 | 57.1 | Python, SQL, Estadística | Machine Learning | Valentina Rojas, Julián Torres, Daniela Vargas | 1 | True |
| Natalia Suárez | 60.0 | 42.9 | Python, Estadística | SQL, Machine Learning | Valentina Rojas, Daniela Vargas | 2 | False |
| Sebastián Pardo | 60.0 | 42.9 | Python, Machine Learning | SQL, Estadística | Valentina Rojas, Julián Torres, Daniela Vargas | 1 | False |
| Camila Herrera | 55.0 | 42.9 | SQL, Estadística | Python, Machine Learning | Valentina Rojas | 3 | False |
| David Cardona | 55.0 | 42.9 | Python, SQL | Machine Learning, Estadística | Valentina Rojas | 3 | False |
| Mariana López | 55.0 | 57.1 | Python, Machine Learning | SQL, Estadística | Daniela Vargas | 1 | False |

## 5. ¿Qué proyectos comparten tecnologías o miembros relacionados?

| proyecto_a | proyecto_b | tecnologias_compartidas | miembros_compartidos | pares_conectados | puntaje |
|---|---|---|---|---|---|
| Motor de Scoring Crediticio | Lago de Datos en la Nube | Python, SQL, Spark | Felipe Ramírez | 6 | 15 |
| Plataforma de Comercio Electrónico | Red Social Interna con Grafos | React, Docker | Alejandro Restrepo | 7 | 14 |
| App de Domicilios | Rediseño de Banca Móvil | Kotlin, Figma | Tomás Arango, Valeria Fontalvo | 3 | 13 |
| Migración a Kubernetes | Lago de Datos en la Nube | AWS, Terraform | Diana Valencia | 5 | 12 |
| Motor de Scoring Crediticio | Recomendador de Cursos | Python, Machine Learning |  | 7 | 11 |
| Portal Educativo | Rediseño de Banca Móvil | Figma, UX Research | Fernando De la Hoz | 3 | 10 |
| Motor de Scoring Crediticio | Tablero de Indicadores Nacionales | SQL |  | 8 | 10 |
| Tablero de Indicadores Nacionales | Recomendador de Cursos |  | Daniela Vargas, Juliana Escorcia | 4 | 10 |

## 6. ¿Qué habilidades son las más demandadas en las ofertas?

| habilidad | categoria | ofertas | obligatoria_en | profesionales_que_la_tienen |
|---|---|---|---|---|
| Python | Datos e IA | 11 | 9 | 20 |
| Docker | Cloud y DevOps | 6 | 1 | 11 |
| Linux | Cloud y DevOps | 5 | 4 | 9 |
| SQL | Datos e IA | 5 | 4 | 9 |
| Redes | Seguridad y redes | 3 | 3 | 7 |
| AWS | Cloud y DevOps | 3 | 2 | 6 |
| Estadística | Datos e IA | 3 | 2 | 6 |
| Power BI | Datos e IA | 3 | 2 | 7 |
| Figma | Producto y diseño | 3 | 1 | 6 |
| Ciberseguridad | Seguridad y redes | 2 | 2 | 4 |

## Recomendaciones de contactos, empleos y colaboradores

Contactos para **Julián Torres**:

| nombre | puntaje | comunes | habilidades_compartidas | empresa_compartida |
|---|---|---|---|---|
| Daniela Vargas | 17 | Sebastián Pardo, Valentina Rojas, Laura Castillo | Python, Power BI | Andina Analytics |
| Andrés Gómez | 9 | Valentina Rojas | Python, SQL | Andina Analytics |
| Camila Herrera | 9 | Valentina Rojas | SQL, Power BI |  |
| Juliana Escorcia | 8 |  | Python, SQL, Power BI |  |
| Natalia Suárez | 8 | Valentina Rojas, Laura Castillo | Python |  |

Empleos para **Elena Ríos** (sin conexiones: solo pesa la cobertura de habilidades):

| oferta | empresa | puntaje | cobertura_pct | cumple | faltan |
|---|---|---|---|---|---|
| Analista de Riesgo con Machine Learning | BancoNorte Digital | 30.0 | 42.9 | Python, Estadística, Power BI | Machine Learning |
| Científico de Datos Semi Senior | Andina Analytics | 30.0 | 42.9 | Python, SQL, Estadística | Machine Learning |
| Ingeniero de Grafos Neo4j | Cumbre Talento | 23.3 | 33.3 | Python, SQL | Neo4j, Docker |
| Ingeniero de Datos | Andina Analytics | 20.0 | 28.6 | Python, SQL | Spark, AWS |
| Desarrollador Python / Django | Paisa Software | 11.7 | 16.7 | Python | Django, PostgreSQL |

Empleos para **David Cardona**:

| oferta | empresa | puntaje | cobertura_pct | contactos_en_empresa | contactos_2do_grado |
|---|---|---|---|---|---|
| Desarrollador Backend Python | BancoNorte Digital | 65.0 | 85.7 |  | 1 |
| Ingeniero de Grafos Neo4j | Cumbre Talento | 63.3 | 83.3 |  | 1 |
| Científico de Datos Semi Senior | Andina Analytics | 55.0 | 42.9 | Valentina Rojas | 3 |
| Ingeniero de Datos | Andina Analytics | 55.0 | 42.9 | Valentina Rojas | 3 |
| Desarrollador Full Stack | Paisa Software | 50.0 | 28.6 | Alejandro Restrepo, Juan Pablo Henao, Esteban Uribe | 1 |

Colaboradores para **Valentina Rojas**:

| nombre | puntaje | tecnologias_que_aporta | conectado | contactos_en_comun |
|---|---|---|---|---|
| Sebastián Pardo | 12 | Python, Machine Learning, Docker | True | 3 |
| Daniela Vargas | 10 | Python, Machine Learning | True | 3 |
| Andrés Gómez | 9 | Python, SQL, Spark | True | 0 |
| Julián Torres | 9 | Python, SQL | True | 2 |
| Natalia Suárez | 8 | Python | True | 3 |

## Panel de analítica
### Usuarios más influyentes

| nombre | conexiones | pagerank | intermediacion | indice_influencia |
|---|---|---|---|---|
| Alejandro Restrepo | 11 | 0.0547 | 0.2966 | 100.0 |
| Carolina Barrios | 8 | 0.0537 | 0.216 | 81.2 |
| Carlos Mosquera | 10 | 0.0541 | 0.1568 | 80.9 |
| Valentina Rojas | 9 | 0.0451 | 0.1965 | 76.8 |
| Daniela Vargas | 8 | 0.0422 | 0.1612 | 68.1 |
| Juan Pablo Henao | 6 | 0.0318 | 0.1332 | 52.5 |
| Sebastián Pardo | 6 | 0.0306 | 0.134 | 51.9 |
| Diana Valencia | 5 | 0.0272 | 0.1167 | 44.8 |

### Comunidades — louvain (modularidad = 0.6293)

| comunidad | tamano | ciudad_predominante | habilidades_predominantes | empresas_predominantes |
|---|---|---|---|---|
| 1 | 11 | Bogotá | Python (9), SQL (6), Machine Learning (5), Deep Learning (4) | Andina Analytics (4), BancoNorte Digital (3), SaludMente IA (3) |
| 2 | 11 | Medellín | JavaScript (7), React (5), TypeScript (4), Figma (3) | Paisa Software (4), MoviApps Labs (3), TiendaRápida (3) |
| 3 | 10 | Cali | Linux (7), Docker (6), Redes (5), Ciberseguridad (4) | CiberEscudo (4), Pacífico Cloud (4), BancoNorte Digital (1) |
| 4 | 8 | Barranquilla | Comunicación (5), Scrum (4), Figma (3), Gestión de Producto (3) | Caribe Creativo (3), EduConecta (3), Cumbre Talento (1) |
| 5 | 2 | Bucaramanga | Linux (2), Python (2), Redes (2), Docker (1) | Santander IoT (2) |
| 6 | 1 | Bogotá | Estadística (1), Power BI (1), Python (1), SQL (1) |  |

### Comunidades — componentes (modularidad = 0.0235)

| comunidad | tamano | ciudad_predominante | habilidades_predominantes | empresas_predominantes |
|---|---|---|---|---|
| 1 | 40 | Bogotá | Python (17), Docker (10), Liderazgo (9), Comunicación (8) | TiendaRápida (5), Andina Analytics (4), BancoNorte Digital (4) |
| 2 | 2 | Bucaramanga | Linux (2), Python (2), Redes (2), Docker (1) | Santander IoT (2) |
| 3 | 1 | Bogotá | Estadística (1), Power BI (1), Python (1), SQL (1) |  |

## Resultado de las pruebas automáticas

```
...............................................................          [100%]
63 passed in 339.47s (0:05:39)
```
