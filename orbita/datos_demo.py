"""Datos ficticios de demostración (deterministas, semilla 42).

Diseño intencional para que todas las consultas den resultados interesantes:
- 4 comunidades densas por área/ciudad (Datos-IA Bogotá, Web-Móvil Medellín,
  Cloud-Seguridad Cali, Producto-Diseño Barranquilla) unidas por pocos "puentes".
- 1 componente aislado (IoT Bucaramanga) y 1 usuaria sin conexiones (recién egresada).
- Ofertas con habilidades obligatorias/deseables y niveles mínimos, 2 ofertas cerradas.

La carga usa MERGE: ejecutarla varias veces NO duplica datos y NO borra nada.
Todos los nombres, correos y empresas son ficticios.
"""
from __future__ import annotations

import random

from .db import escribir
from .seguridad import hash_password

# Todos los nodos de demostración llevan la propiedad demo = LOTE para poder eliminarlos
# selectivamente sin tocar los datos creados por usuarios reales.
LOTE = "orbita-demo"
# Contraseña COMPARTIDA de las cuentas ficticias de demostración (no es una credencial real).
PASSWORD_DEMO = "Demo2026*"
RECLUTADORES = {"U003", "U009", "U023", "U033"}  # reclutadores de Cumbre Talento, Andina Analytics, Pacífico Cloud, EduConecta

HABILIDADES = {
    "Datos e IA": ["Python", "SQL", "Machine Learning", "Deep Learning", "NLP", "Estadística", "Power BI", "Spark"],
    "Desarrollo": ["JavaScript", "TypeScript", "React", "Node.js", "Django", "HTML/CSS", "Flutter", "Kotlin", "Swift"],
    "Bases de datos": ["PostgreSQL", "MongoDB", "Neo4j"],
    "Cloud y DevOps": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux"],
    "Seguridad y redes": ["Ciberseguridad", "Redes"],
    "Producto y diseño": ["Figma", "UX Research", "Diseño UI", "Gestión de Producto", "Scrum"],
    "Habilidades blandas": ["Liderazgo", "Comunicación", "Inglés"],
}

EMPRESAS = [
    ("E01", "Andina Analytics", "Datos y analítica", "Bogotá", "Mediana"),
    ("E02", "BancoNorte Digital", "Banca y finanzas", "Bogotá", "Grande"),
    ("E03", "SaludMente IA", "Salud digital", "Bogotá", "Startup"),
    ("E04", "Paisa Software", "Desarrollo de software", "Medellín", "Mediana"),
    ("E05", "TiendaRápida", "Comercio electrónico", "Medellín", "Grande"),
    ("E06", "MoviApps Labs", "Aplicaciones móviles", "Medellín", "Pequeña"),
    ("E07", "Pacífico Cloud", "Servicios en la nube", "Cali", "Mediana"),
    ("E08", "CiberEscudo", "Ciberseguridad", "Cali", "Pequeña"),
    ("E09", "Caribe Creativo", "Diseño digital", "Barranquilla", "Pequeña"),
    ("E10", "EduConecta", "Tecnología educativa", "Barranquilla", "Startup"),
    ("E11", "Santander IoT", "Electrónica e IoT", "Bucaramanga", "Pequeña"),
    ("E12", "Cumbre Talento", "Consultoría de talento TI", "Bogotá", "Mediana"),
]

# id, nombre, titular, ciudad, años, grupo, habilidades
USUARIOS = [
    ("U001", "Valentina Rojas", "Científica de Datos Senior", "Bogotá", 9, "A", ["Python", "Machine Learning", "SQL", "Estadística", "Neo4j", "Liderazgo", "Inglés", "Deep Learning"]),
    ("U002", "Andrés Gómez", "Ingeniero de Datos", "Bogotá", 5, "A", ["Python", "SQL", "Spark", "AWS", "PostgreSQL"]),
    ("U003", "Camila Herrera", "Analista de Inteligencia de Negocios", "Bogotá", 4, "A", ["Power BI", "SQL", "Estadística", "Comunicación"]),
    ("U004", "Santiago Morales", "Ingeniero de Machine Learning", "Bogotá", 6, "A", ["Python", "Machine Learning", "Deep Learning", "Spark", "Docker"]),
    ("U005", "Laura Castillo", "Analista de Riesgo Cuantitativo", "Bogotá", 7, "A", ["Estadística", "Python", "Power BI", "SQL"]),
    ("U006", "Felipe Ramírez", "Arquitecto de Datos", "Bogotá", 11, "A", ["SQL", "Spark", "AWS", "PostgreSQL", "Terraform", "Liderazgo"]),
    ("U007", "Mariana López", "Especialista en Procesamiento de Lenguaje Natural", "Bogotá", 4, "A", ["NLP", "Python", "Deep Learning", "Machine Learning", "Inglés"]),
    ("U008", "Julián Torres", "Analista de Datos Junior", "Bogotá", 1, "A", ["SQL", "Power BI", "Python"]),
    ("U009", "Daniela Vargas", "Líder de Analítica", "Bogotá", 10, "A", ["Python", "Machine Learning", "Power BI", "Liderazgo", "Comunicación", "Gestión de Producto"]),
    ("U010", "Sebastián Pardo", "Ingeniero MLOps", "Bogotá", 6, "A", ["Python", "Docker", "Kubernetes", "Machine Learning", "CI/CD", "AWS"]),
    ("U011", "Natalia Suárez", "Investigadora en Inteligencia Artificial", "Bogotá", 5, "A", ["Deep Learning", "NLP", "Python", "Estadística", "Inglés"]),
    ("U012", "Alejandro Restrepo", "Desarrollador Full Stack Senior", "Medellín", 9, "B", ["JavaScript", "TypeScript", "React", "Node.js", "MongoDB", "Docker", "Neo4j", "Liderazgo"]),
    ("U013", "Isabella Mejía", "Desarrolladora Frontend", "Medellín", 3, "B", ["React", "JavaScript", "HTML/CSS", "TypeScript", "Figma"]),
    ("U014", "Mateo Giraldo", "Desarrollador Backend Node.js", "Medellín", 4, "B", ["Node.js", "JavaScript", "MongoDB", "PostgreSQL", "Docker"]),
    ("U015", "Sara Ochoa", "Desarrolladora Móvil Flutter", "Medellín", 3, "B", ["Flutter", "Kotlin", "Figma", "JavaScript"]),
    ("U016", "Tomás Arango", "Desarrollador Android", "Medellín", 5, "B", ["Kotlin", "Flutter", "Swift"]),
    ("U017", "Manuela Zapata", "Ingeniera de Calidad de Software", "Medellín", 4, "B", ["JavaScript", "CI/CD", "Python", "Comunicación"]),
    ("U018", "Juan Pablo Henao", "Líder Técnico", "Medellín", 10, "B", ["React", "Node.js", "TypeScript", "Liderazgo", "Scrum", "AWS"]),
    ("U019", "Luisa Echeverri", "Desarrolladora React", "Medellín", 2, "B", ["React", "TypeScript", "HTML/CSS", "JavaScript"]),
    ("U020", "David Cardona", "Desarrollador Python / Django", "Medellín", 5, "B", ["Python", "Django", "PostgreSQL", "React", "SQL", "Neo4j"]),
    ("U021", "Paula Montoya", "Desarrolladora iOS", "Medellín", 4, "B", ["Swift", "Figma", "Inglés"]),
    ("U022", "Esteban Uribe", "Desarrollador Web Junior", "Medellín", 1, "B", ["HTML/CSS", "JavaScript", "Python"]),
    ("U023", "Carlos Mosquera", "Líder DevOps", "Cali", 11, "C", ["Docker", "Kubernetes", "Terraform", "AWS", "Linux", "CI/CD", "Liderazgo"]),
    ("U024", "Diana Valencia", "Arquitecta Cloud AWS", "Cali", 8, "C", ["AWS", "Terraform", "Kubernetes", "Docker", "Python"]),
    ("U025", "Andrés Caicedo", "Especialista en Ciberseguridad", "Cali", 9, "C", ["Ciberseguridad", "Redes", "Linux", "Python"]),
    ("U026", "Gabriela Lozano", "Ingeniera de Confiabilidad (SRE)", "Cali", 6, "C", ["Kubernetes", "Linux", "Docker", "Python", "CI/CD"]),
    ("U027", "Ricardo Palacios", "Administrador de Redes", "Cali", 12, "C", ["Redes", "Linux", "Ciberseguridad"]),
    ("U028", "Verónica Ospina", "Ingeniera de Plataforma", "Cali", 5, "C", ["Kubernetes", "Terraform", "Docker", "Azure"]),
    ("U029", "Jorge Escobar", "Pentester", "Cali", 6, "C", ["Ciberseguridad", "Python", "Linux", "Redes"]),
    ("U030", "Melissa Rentería", "Ingeniera Cloud Azure", "Cali", 3, "C", ["Azure", "CI/CD", "Docker", "Linux"]),
    ("U031", "Óscar Bermúdez", "Ingeniero de Infraestructura", "Cali", 8, "C", ["Linux", "Redes", "Azure", "Docker"]),
    ("U032", "Ximena Holguín", "Analista de Centro de Operaciones de Seguridad", "Cali", 2, "C", ["Ciberseguridad", "Redes", "Inglés"]),
    ("U033", "Carolina Barrios", "Gerente de Producto", "Barranquilla", 9, "D", ["Gestión de Producto", "Scrum", "UX Research", "Liderazgo", "Comunicación", "Inglés"]),
    ("U034", "Fernando De la Hoz", "Diseñador UX/UI", "Barranquilla", 6, "D", ["Figma", "Diseño UI", "UX Research", "HTML/CSS"]),
    ("U035", "Andrea Polo", "Investigadora de Experiencia de Usuario", "Barranquilla", 4, "D", ["UX Research", "Figma", "Comunicación"]),
    ("U036", "Luis Charris", "Scrum Master", "Barranquilla", 7, "D", ["Scrum", "Liderazgo", "Comunicación"]),
    ("U037", "Valeria Fontalvo", "Diseñadora de Interfaces", "Barranquilla", 3, "D", ["Diseño UI", "Figma", "HTML/CSS"]),
    ("U038", "Miguel Ángel Pérez", "Product Owner", "Barranquilla", 6, "D", ["Gestión de Producto", "Scrum", "Comunicación", "Power BI"]),
    ("U039", "Juliana Escorcia", "Analista de Producto", "Barranquilla", 4, "D", ["SQL", "Power BI", "Estadística", "Gestión de Producto", "Python"]),
    ("U040", "Ricardo Navarro", "Coach Ágil", "Barranquilla", 13, "D", ["Scrum", "Liderazgo", "Comunicación", "Inglés"]),
    ("U041", "Sofía Cárdenas", "Ingeniera de IoT", "Bucaramanga", 5, "E", ["Python", "Linux", "Redes", "Docker"]),
    ("U042", "Hernán Quintero", "Desarrollador de Sistemas Embebidos", "Bucaramanga", 7, "E", ["Linux", "Python", "Redes"]),
    ("U043", "Elena Ríos", "Ingeniera de Sistemas recién egresada", "Bogotá", 0, "F", ["Python", "SQL", "Power BI", "Estadística"]),
]

# usuario, empresa, cargo, desde, actual
EMPLEOS = [
    ("U001", "E01", "Científica de Datos Senior", 2020, True), ("U001", "E02", "Analista de Datos", 2016, False),
    ("U002", "E01", "Ingeniero de Datos", 2021, True), ("U003", "E12", "Analista BI", 2022, True),
    ("U004", "E02", "Ingeniero de ML", 2021, True), ("U004", "E01", "Científico de Datos", 2019, False),
    ("U005", "E02", "Analista de Riesgo", 2019, True), ("U006", "E02", "Arquitecto de Datos", 2018, True),
    ("U007", "E03", "Especialista NLP", 2022, True), ("U008", "E01", "Analista Junior", 2024, True),
    ("U009", "E01", "Líder de Analítica", 2019, True), ("U010", "E03", "Ingeniero MLOps", 2023, True),
    ("U010", "E07", "Ingeniero DevOps", 2020, False), ("U011", "E03", "Investigadora", 2021, True),
    ("U012", "E04", "Full Stack Senior", 2019, True), ("U012", "E05", "Desarrollador Web", 2016, False),
    ("U013", "E05", "Desarrolladora Frontend", 2022, True), ("U014", "E04", "Desarrollador Backend", 2021, True),
    ("U015", "E06", "Desarrolladora Móvil", 2022, True), ("U016", "E06", "Desarrollador Android", 2020, True),
    ("U017", "E05", "Ingeniera QA", 2021, True), ("U018", "E04", "Líder Técnico", 2018, True),
    ("U019", "E05", "Desarrolladora React", 2023, True), ("U020", "E10", "Desarrollador Django", 2022, True),
    ("U020", "E04", "Desarrollador Python", 2019, False), ("U021", "E06", "Desarrolladora iOS", 2021, True),
    ("U022", "E04", "Desarrollador Junior", 2024, True), ("U023", "E07", "Líder DevOps", 2017, True),
    ("U024", "E07", "Arquitecta Cloud", 2019, True), ("U025", "E08", "Especialista en Seguridad", 2018, True),
    ("U026", "E05", "SRE", 2022, True), ("U026", "E07", "Ingeniera Cloud", 2019, False),
    ("U027", "E08", "Administrador de Redes", 2016, True), ("U028", "E07", "Ingeniera de Plataforma", 2021, True),
    ("U029", "E08", "Pentester", 2020, True), ("U030", "E07", "Ingeniera Cloud Azure", 2023, True),
    ("U031", "E02", "Ingeniero de Infraestructura", 2020, True), ("U032", "E08", "Analista SOC", 2023, True),
    ("U033", "E10", "Gerente de Producto", 2020, True), ("U033", "E04", "Product Owner", 2017, False),
    ("U034", "E09", "Diseñador UX/UI", 2019, True), ("U035", "E09", "Investigadora UX", 2021, True),
    ("U036", "E10", "Scrum Master", 2021, True), ("U037", "E09", "Diseñadora UI", 2022, True),
    ("U038", "E05", "Product Owner", 2020, True), ("U039", "E10", "Analista de Producto", 2022, True),
    ("U039", "E01", "Analista de Datos", 2020, False), ("U040", "E12", "Coach Ágil", 2019, True),
    ("U041", "E11", "Ingeniera IoT", 2020, True), ("U042", "E11", "Ingeniero de Embebidos", 2021, True),
]

HUBS = {"A": ["U001", "U009"], "B": ["U012"], "C": ["U023"], "D": ["U033"]}

PUENTES = [  # conexiones entre comunidades
    ("U001", "U020"), ("U010", "U023"), ("U018", "U033"), ("U039", "U009"),
    ("U012", "U024"), ("U026", "U010"), ("U001", "U012"), ("U034", "U013"), ("U017", "U030"),
]

# id, nombre, descripción, estado, año, tecnologías, [(miembro, rol)]
PROYECTOS = [
    ("P01", "Motor de Scoring Crediticio", "Modelo de riesgo para aprobación de créditos.", "Finalizado", 2023,
     ["Python", "Machine Learning", "SQL", "Spark"], [("U004", "Líder técnico"), ("U005", "Analista"), ("U001", "Asesora"), ("U006", "Arquitecto")]),
    ("P02", "Chatbot Clínico", "Asistente conversacional para triaje de pacientes.", "En curso", 2024,
     ["NLP", "Python", "Deep Learning", "Docker"], [("U007", "Líder técnica"), ("U011", "Investigadora"), ("U010", "MLOps")]),
    ("P03", "Tablero de Indicadores Nacionales", "Visualización de indicadores socioeconómicos abiertos.", "Finalizado", 2022,
     ["Power BI", "SQL", "Estadística"], [("U003", "Desarrolladora BI"), ("U008", "Analista"), ("U009", "Directora"), ("U039", "Analista")]),
    ("P04", "Plataforma de Comercio Electrónico", "Tienda en línea de alto tráfico.", "En curso", 2024,
     ["React", "Node.js", "MongoDB", "Docker"], [("U012", "Arquitecto"), ("U014", "Backend"), ("U019", "Frontend"), ("U017", "QA")]),
    ("P05", "App de Domicilios", "Aplicación móvil para pedidos y entregas.", "En curso", 2025,
     ["Flutter", "Kotlin", "Node.js", "Figma"], [("U015", "Líder móvil"), ("U016", "Android"), ("U018", "Líder técnico"), ("U037", "Diseño")]),
    ("P06", "Portal Educativo", "Plataforma de cursos virtuales.", "En curso", 2025,
     ["React", "Django", "PostgreSQL", "Figma", "UX Research"], [("U020", "Backend"), ("U034", "Diseño UX"), ("U035", "Investigación UX"), ("U033", "Producto")]),
    ("P07", "Migración a Kubernetes", "Contenerización de servicios heredados.", "Finalizado", 2024,
     ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD"], [("U023", "Líder"), ("U026", "SRE"), ("U028", "Plataforma"), ("U024", "Arquitecta")]),
    ("P08", "Centro de Operaciones de Seguridad", "Monitoreo de amenazas 24/7.", "En curso", 2024,
     ["Ciberseguridad", "Linux", "Redes", "Python"], [("U025", "Líder"), ("U029", "Pentester"), ("U032", "Analista SOC")]),
    ("P09", "Lago de Datos en la Nube", "Centralización de datos corporativos en AWS.", "En curso", 2025,
     ["Spark", "AWS", "Python", "Terraform", "SQL"], [("U002", "Ingeniero de datos"), ("U006", "Arquitecto"), ("U024", "Cloud"), ("U010", "MLOps")]),
    ("P10", "Red Social Interna con Grafos", "Red de conocimiento corporativa sobre Neo4j.", "Propuesta", 2025,
     ["Neo4j", "Python", "React", "Docker"], [("U001", "Líder"), ("U012", "Full Stack"), ("U020", "Backend"), ("U013", "Frontend")]),
    ("P11", "Rediseño de Banca Móvil", "Nueva experiencia de la app bancaria.", "En curso", 2025,
     ["Figma", "Diseño UI", "UX Research", "Swift", "Kotlin"], [("U034", "Líder de diseño"), ("U037", "UI"), ("U021", "iOS"), ("U016", "Android")]),
    ("P12", "Sistema de Monitoreo IoT", "Sensores industriales con alertas en tiempo real.", "En curso", 2024,
     ["Python", "Linux", "Redes", "Docker"], [("U041", "Líder"), ("U042", "Embebidos")]),
    ("P13", "Recomendador de Cursos", "Sistema de recomendación para estudiantes.", "Propuesta", 2025,
     ["Machine Learning", "Python", "Django", "PostgreSQL"], [("U009", "Directora"), ("U011", "Investigadora"), ("U039", "Producto"), ("U020", "Backend")]),
    ("P14", "Automatización CI/CD Corporativa", "Pipelines de despliegue continuo.", "Finalizado", 2023,
     ["CI/CD", "Docker", "Azure", "Linux"], [("U030", "Cloud"), ("U031", "Infraestructura"), ("U017", "QA")]),
    ("P15", "Gestión Ágil de Producto", "Transformación ágil de equipos de producto.", "En curso", 2024,
     ["Scrum", "Gestión de Producto", "Liderazgo", "Comunicación"], [("U036", "Scrum Master"), ("U038", "Product Owner"), ("U040", "Coach"), ("U033", "Patrocinadora")]),
]

# id, empresa, título, ciudad, modalidad, nivel, salario, activa, [(habilidad, nivel_min, obligatoria)]
OFERTAS = [
    ("O01", "E01", "Científico de Datos Semi Senior", "Bogotá", "Híbrido", "Semi Senior", 9_000_000, True,
     [("Python", 4, True), ("Machine Learning", 3, True), ("SQL", 3, True), ("Estadística", 3, False)]),
    ("O02", "E01", "Ingeniero de Datos", "Bogotá", "Remoto", "Senior", 11_000_000, True,
     [("Spark", 3, True), ("SQL", 4, True), ("Python", 3, True), ("AWS", 3, False)]),
    ("O03", "E02", "Analista de Riesgo con Machine Learning", "Bogotá", "Presencial", "Semi Senior", 8_500_000, True,
     [("Python", 3, True), ("Estadística", 4, True), ("Machine Learning", 3, True), ("Power BI", 2, False)]),
    ("O04", "E02", "Desarrollador Backend Python", "Bogotá", "Híbrido", "Semi Senior", 8_000_000, True,
     [("Python", 3, True), ("Django", 3, True), ("PostgreSQL", 3, True), ("Docker", 2, False)]),
    ("O05", "E02", "Especialista en Ciberseguridad", "Bogotá", "Presencial", "Senior", 12_000_000, True,
     [("Ciberseguridad", 4, True), ("Redes", 3, True), ("Linux", 3, True)]),
    ("O06", "E03", "Ingeniero de NLP", "Bogotá", "Remoto", "Senior", 12_500_000, True,
     [("NLP", 4, True), ("Deep Learning", 3, True), ("Python", 4, True), ("Docker", 2, False)]),
    ("O07", "E04", "Desarrollador Full Stack", "Medellín", "Híbrido", "Semi Senior", 7_500_000, True,
     [("React", 3, True), ("Node.js", 3, True), ("TypeScript", 3, True), ("MongoDB", 2, False)]),
    ("O08", "E04", "Desarrollador Python / Django", "Medellín", "Remoto", "Junior", 4_500_000, True,
     [("Python", 2, True), ("Django", 2, True), ("PostgreSQL", 2, True)]),
    ("O09", "E05", "Desarrollador Frontend React", "Medellín", "Híbrido", "Junior", 5_000_000, True,
     [("React", 3, True), ("TypeScript", 2, True), ("HTML/CSS", 3, True), ("Figma", 2, False)]),
    ("O10", "E05", "Ingeniero de Confiabilidad (SRE)", "Medellín", "Remoto", "Senior", 11_000_000, True,
     [("Kubernetes", 4, True), ("AWS", 3, True), ("Linux", 3, True), ("CI/CD", 3, False)]),
    ("O11", "E06", "Desarrollador Flutter", "Medellín", "Presencial", "Semi Senior", 6_500_000, True,
     [("Flutter", 3, True), ("Kotlin", 2, False), ("Figma", 2, False)]),
    ("O12", "E06", "Desarrollador iOS", "Medellín", "Presencial", "Semi Senior", 7_000_000, False,
     [("Swift", 3, True), ("Figma", 2, False)]),
    ("O13", "E07", "Arquitecto Cloud", "Cali", "Remoto", "Senior", 13_000_000, True,
     [("AWS", 4, True), ("Terraform", 3, True), ("Kubernetes", 3, True), ("Docker", 3, False)]),
    ("O14", "E07", "Ingeniero DevOps Azure", "Cali", "Híbrido", "Semi Senior", 8_500_000, True,
     [("Azure", 3, True), ("CI/CD", 3, True), ("Docker", 3, True), ("Linux", 2, False)]),
    ("O15", "E08", "Analista SOC", "Cali", "Presencial", "Junior", 4_800_000, True,
     [("Ciberseguridad", 2, True), ("Redes", 2, True), ("Linux", 2, True), ("Python", 2, False)]),
    ("O16", "E09", "Diseñador UX/UI", "Barranquilla", "Remoto", "Semi Senior", 6_000_000, True,
     [("Figma", 3, True), ("UX Research", 3, True), ("Diseño UI", 3, True)]),
    ("O17", "E10", "Gerente de Producto EdTech", "Barranquilla", "Híbrido", "Senior", 10_000_000, True,
     [("Gestión de Producto", 4, True), ("Scrum", 3, True), ("UX Research", 2, False), ("Inglés", 3, True)]),
    ("O18", "E10", "Analista de Datos Educativos", "Barranquilla", "Remoto", "Junior", 4_500_000, True,
     [("SQL", 2, True), ("Power BI", 2, True), ("Python", 2, False), ("Estadística", 2, True)]),
    ("O19", "E11", "Ingeniero IoT", "Bucaramanga", "Presencial", "Semi Senior", 6_000_000, True,
     [("Python", 3, True), ("Linux", 3, True), ("Redes", 3, True), ("Docker", 2, False)]),
    ("O20", "E12", "Consultor de Datos", "Bogotá", "Híbrido", "Junior", 5_000_000, True,
     [("SQL", 2, True), ("Python", 2, True), ("Power BI", 2, True), ("Comunicación", 3, False)]),
    ("O21", "E12", "Ingeniero de Grafos Neo4j", "Bogotá", "Remoto", "Semi Senior", 9_500_000, True,
     [("Neo4j", 3, True), ("Python", 3, True), ("Docker", 2, False), ("SQL", 2, False)]),
    ("O22", "E12", "Scrum Master", "Bogotá", "Híbrido", "Senior", 8_000_000, False,
     [("Scrum", 4, True), ("Liderazgo", 3, True), ("Comunicación", 3, True)]),
]

POSTULACIONES = [
    ("U008", "O01", "Enviada"), ("U005", "O01", "En revisión"), ("U022", "O07", "Enviada"), ("U019", "O07", "Entrevista"),
    ("U020", "O08", "Enviada"), ("U013", "O09", "En revisión"), ("U022", "O09", "Enviada"), ("U028", "O13", "Entrevista"),
    ("U031", "O14", "Enviada"), ("U027", "O05", "Enviada"), ("U029", "O05", "En revisión"), ("U035", "O17", "Enviada"),
    ("U038", "O17", "Entrevista"), ("U003", "O18", "Enviada"), ("U043", "O20", "Enviada"), ("U043", "O18", "Enviada"),
    ("U002", "O21", "En revisión"), ("U012", "O21", "Enviada"), ("U036", "O22", "Enviada"), ("U004", "O06", "Enviada"),
    ("U010", "O13", "Enviada"), ("U017", "O14", "Enviada"), ("U021", "O12", "Rechazada"), ("U034", "O09", "Enviada"),
    ("U009", "O17", "Enviada"),
]


def _slug(nombre: str) -> str:
    tabla = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    partes = nombre.translate(tabla).lower().split()
    return f"{partes[0]}.{partes[-1]}"


def construir() -> dict:
    """Genera de forma determinista todas las filas que se cargarán."""
    rng = random.Random(42)
    categorias = {h: c for c, hs in HABILIDADES.items() for h in hs}

    habilidades = [{"nombre": h, "categoria": c, "demo": LOTE} for h, c in categorias.items()]
    empresas = [{"id": i, "nombre": n, "sector": s, "ciudad": c, "tamano": t, "demo": LOTE,
                 "sitio_web": f"https://{n.lower().replace(' ', '').replace('á', 'a')}.ejemplo.co",
                 "descripcion": f"{n}: empresa ficticia del sector {s.lower()} con sede en {c}."}
                for i, n, s, c, t in EMPRESAS]
    hash_demo = hash_password(PASSWORD_DEMO, sal=b"nexus-demo-sal16")  # sal fija => script .cypher reproducible
    usuarios, tiene = [], []
    for i, (uid, nombre, titular, ciudad, anios, grupo, habs) in enumerate(USUARIOS):
        # IMPORTANTE: el orden de las llamadas a rng no debe cambiar (determina conexiones y niveles).
        nivel_edu = "Pregrado" if anios < 5 else rng.choice(["Especialización", "Maestría", "Pregrado"])
        fecha_reg = f"202{rng.randint(2, 5)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        usuarios.append({"id": uid, "fecha_registro": fecha_reg,
                         "rol": "reclutador" if uid in RECLUTADORES else "profesional", "password_hash": hash_demo,
                         "props": {"nombre": nombre, "email": f"{_slug(nombre)}@ejemplo.com", "titular": titular,
                                   "ciudad": ciudad, "anios_experiencia": anios, "telefono": f"+57 300 {1000000 + i * 7919:07d}",
                                   "nivel_educativo": nivel_edu,
                                   "resumen": f"{titular} con {anios} años de experiencia en {ciudad}.",
                                   "demo": LOTE}})
        for j, h in enumerate(habs):
            base = 5 if anios >= 9 else 4 if anios >= 5 else 3 if anios >= 2 else 2
            tiene.append({"u": uid, "h": h, "nivel": max(1, min(5, base - (1 if j > 3 else 0) + rng.choice([-1, 0, 0, 1])))})

    # Conexiones: densas dentro de cada grupo, hubs muy conectados y algunos puentes
    pares = set()
    grupos: dict[str, list[str]] = {}
    for u in USUARIOS:
        grupos.setdefault(u[5], []).append(u[0])
    for g, miembros in grupos.items():
        if g == "F":
            continue
        for a_i, a in enumerate(miembros):
            for b in miembros[a_i + 1:]:
                prob = 0.85 if (a in HUBS.get(g, []) or b in HUBS.get(g, [])) else 0.33
                if g == "E" or rng.random() < prob:
                    pares.add((a, b))
    for a, b in PUENTES:
        pares.add(tuple(sorted((a, b))))
    conexiones = [{"a": a, "b": b, "desde": f"20{rng.randint(18, 25)}-{rng.randint(1, 12):02d}-01"} for a, b in sorted(pares)]

    trabaja = [{"u": u, "e": e, "cargo": c, "desde": d, "actual": a} for u, e, c, d, a in EMPLEOS]
    proyectos = [{"id": i, "nombre": n, "descripcion": d, "estado": s, "anio": y, "demo": LOTE} for i, n, d, s, y, _, _ in PROYECTOS]
    usa = [{"p": p[0], "h": h} for p in PROYECTOS for h in p[5]]
    participa = [{"u": u, "p": p[0], "rol": r} for p in PROYECTOS for u, r in p[6]]
    ofertas = [{"id": i, "empresa": e, "titulo": t, "ciudad": c, "modalidad": m, "nivel": n, "salario": s, "activa": a, "demo": LOTE,
                "descripcion": f"{t} para {dict((x[0], x[1]) for x in EMPRESAS)[e]} ({m.lower()}).",
                "fecha": f"2025-{(k % 12) + 1:02d}-{(k * 3) % 27 + 1:02d}"}
               for k, (i, e, t, c, m, n, s, a, _) in enumerate(OFERTAS)]
    requiere = [{"o": o[0], "h": h, "nivel_minimo": nv, "obligatoria": ob} for o in OFERTAS for h, nv, ob in o[8]]
    postula = [{"u": u, "o": o, "estado": e, "fecha": f"2025-{rng.randint(6, 11):02d}-{rng.randint(1, 28):02d}"}
               for u, o, e in POSTULACIONES]
    return dict(habilidades=habilidades, empresas=empresas, usuarios=usuarios, tiene=tiene, conexiones=conexiones,
                trabaja=trabaja, proyectos=proyectos, usa=usa, participa=participa, ofertas=ofertas,
                requiere=requiere, postula=postula)


# ---------------------------------------------------------------- Consultas de carga (idempotentes)
CARGA = [
    ("habilidades", """UNWIND $filas AS f
MERGE (h:Habilidad {nombre: f.nombre}) SET h.categoria = f.categoria, h.demo = f.demo"""),
    ("empresas", """UNWIND $filas AS f
MERGE (e:Empresa {id: f.id}) SET e += f"""),
    ("usuarios", """UNWIND $filas AS f
MERGE (u:Usuario {id: f.id})
SET u += f.props, u.fecha_registro = date(f.fecha_registro),
    u.rol = coalesce(u.rol, f.rol),
    u.password_hash = coalesce(u.password_hash, f.password_hash),
    u.activo = coalesce(u.activo, true),
    u.intentos_fallidos = coalesce(u.intentos_fallidos, 0)"""),
    ("tiene", """UNWIND $filas AS f
MATCH (u:Usuario {id: f.u}), (h:Habilidad {nombre: f.h})
MERGE (u)-[r:TIENE_HABILIDAD]->(h) SET r.nivel = f.nivel"""),
    ("conexiones", """UNWIND $filas AS f
MATCH (a:Usuario {id: f.a}), (b:Usuario {id: f.b})
WHERE NOT (b)-[:CONECTA_CON]->(a)
MERGE (a)-[r:CONECTA_CON]->(b) ON CREATE SET r.desde = date(f.desde)"""),
    ("trabaja", """UNWIND $filas AS f
MATCH (u:Usuario {id: f.u}), (e:Empresa {id: f.e})
MERGE (u)-[r:TRABAJA_EN]->(e) SET r.cargo = f.cargo, r.desde = f.desde, r.actual = f.actual"""),
    ("proyectos", """UNWIND $filas AS f
MERGE (p:Proyecto {id: f.id}) SET p += f"""),
    ("usa", """UNWIND $filas AS f
MATCH (p:Proyecto {id: f.p}), (h:Habilidad {nombre: f.h})
MERGE (p)-[:USA_TECNOLOGIA]->(h)"""),
    ("participa", """UNWIND $filas AS f
MATCH (u:Usuario {id: f.u}), (p:Proyecto {id: f.p})
MERGE (u)-[r:PARTICIPA_EN]->(p) SET r.rol = f.rol"""),
    ("ofertas", """UNWIND $filas AS f
MATCH (e:Empresa {id: f.empresa})
MERGE (o:Oferta {id: f.id})
SET o.titulo = f.titulo, o.ciudad = f.ciudad, o.modalidad = f.modalidad, o.nivel = f.nivel,
    o.salario = f.salario, o.activa = f.activa, o.descripcion = f.descripcion, o.demo = f.demo,
    o.fecha_publicacion = date(f.fecha)
MERGE (e)-[p:PUBLICA]->(o) ON CREATE SET p.fecha = date(f.fecha)"""),
    ("requiere", """UNWIND $filas AS f
MATCH (o:Oferta {id: f.o}), (h:Habilidad {nombre: f.h})
MERGE (o)-[r:REQUIERE]->(h) SET r.nivel_minimo = f.nivel_minimo, r.obligatoria = f.obligatoria"""),
    ("postula", """UNWIND $filas AS f
MATCH (u:Usuario {id: f.u}), (o:Oferta {id: f.o})
MERGE (u)-[r:POSTULA_A]->(o) ON CREATE SET r.fecha = date(f.fecha), r.estado = f.estado"""),
]


def cargar() -> dict[str, int]:
    datos = construir()
    resumen = {}
    for clave, q in CARGA:
        escribir(q, filas=datos[clave])
        resumen[clave] = len(datos[clave])
    return resumen


# ---------------------------------------------------------------- Exportación a script .cypher
def _lit(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_lit(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_lit(x) for x in v) + "]"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def script_cypher() -> str:
    """Genera un script Cypher autocontenido equivalente a cargar() (para Neo4j Browser / cypher-shell)."""
    datos = construir()
    partes = ["// Datos de demostración de Órbita (generado por scripts/exportar_cypher.py)",
              "// Idempotente: usa MERGE. Ejecutar después de 01_esquema.cypher.", ""]
    for clave, q in CARGA:
        partes.append(f"// ---- {clave} ({len(datos[clave])} filas)")
        partes.append(q.replace("UNWIND $filas AS f", f"UNWIND {_lit(datos[clave])} AS f", 1) + ";")
        partes.append("")
    return "\n".join(partes)
