# Órbita · Red Profesional sobre grafos

Aplicación de networking profesional (estilo LinkedIn) construida con **Python**, **Streamlit** y **Neo4j AuraDB**. Desarrollada para el proyecto I+D de Bases de Datos: *Bases de datos orientadas a grafos*.

Permite gestionar usuarios, empresas, habilidades, proyectos y ofertas laborales, y analizar la red: contactos en común, rutas más cortas, recomendaciones de contactos, empleos, colaboradores y candidatos, usuarios influyentes, comunidades y habilidades más demandadas.

## Requisitos

- Python 3.11 o superior
- Una instancia de Neo4j AuraDB (sirve la gratuita, *Free*)

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración de credenciales (`.env`)

1. Copie la plantilla: `copy .env.example .env`
2. Complete los valores con el archivo de credenciales que AuraDB le dio al crear la instancia (`Neo4j-xxxxxxxx-Created-AAAA-MM-DD.txt`):

```dotenv
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=su_contraseña
NEO4J_DATABASE=neo4j
```

`.env` está en `.gitignore`: **nunca** se sube al repositorio y las credenciales no aparecen en el código. Las instancias Free se pausan tras días sin uso; reactívelas en https://console.neo4j.io.

## Puesta en marcha

```powershell
python scripts\verificar_conexion.py     # prueba la conexión y muestra el contenido (no modifica nada)
python scripts\inicializar_bd.py         # crea restricciones y carga los datos de demostración (solo si la base está vacía)
python scripts\crear_admin.py --nombre "Su Nombre" --email su@correo.com   # crea su cuenta de administrador (pide la contraseña oculta)
streamlit run app.py                     # abre http://localhost:8501
```

No hay que crear nada en la consola de AuraDB: la aplicación crea restricciones, índices y nodos por sí sola. Lo único que se configura es el archivo `.env`.

## Cuentas, roles y seguridad

| Rol | Qué puede hacer |
|---|---|
| **Profesional** (por defecto al registrarse) | Editar su perfil, habilidades, experiencia y proyectos; invitar, aceptar y eliminar conexiones; buscar ofertas y postularse; ver sus recomendaciones, rutas, analítica y grafo |
| **Reclutador** | Todo lo anterior + *Mi empresa*: publicar, editar o cerrar ofertas **solo de la empresa donde trabaja actualmente**, gestionar el estado de las postulaciones y ver candidatos recomendados |
| **Administrador** | Todo + CRUD completo de usuarios, empresas, habilidades, proyectos y ofertas; asignar roles; activar o desactivar cuentas; asignar contraseñas temporales; administrar la base |

- Contraseñas con PBKDF2-SHA256 (260 000 iteraciones y sal aleatoria). Política: 8+ caracteres, mayúscula, minúscula, número y símbolo, sin incluir el nombre ni el correo.
- Mensaje genérico ante credenciales incorrectas y bloqueo de 5 minutos tras 5 intentos fallidos.
- Sesión de 8 horas: el token viaja en la URL (`?s=...`) para sobrevivir a recargas y en Neo4j solo se guarda su hash. Se invalida al cerrar sesión, al cambiar la contraseña o si un administrador desactiva la cuenta.
- Los permisos se verifican en el servidor con Cypher, no solo ocultando botones.

**Cuentas de demostración** (ficticias, contraseña común `Demo2026*`): `valentina.rojas@ejemplo.com` (profesional), `elena.rios@ejemplo.com` (profesional sin conexiones), `camila.herrera@ejemplo.com` y `daniela.vargas@ejemplo.com` (reclutadoras).

## Datos de demostración: verificar, conservar o eliminar

Los 129 nodos de demostración llevan la propiedad `demo = 'orbita-demo'`; lo que se crea desde la aplicación no la lleva.

- **Verificar:** *Administración → Base de datos → Origen de los datos*, o en la consola de AuraDB: `MATCH (n) RETURN labels(n)[0] AS tipo, n.demo IS NOT NULL AS demo, count(*)`.
- **Eliminar solo la demostración:** *Administración → Base de datos → Eliminar solo los datos de demostración* (escribir `BORRAR DEMO`). Conserva todo lo real, incluidas las habilidades y empresas que ya usen sus usuarios.
- **Restaurar la demostración:** `python scripts\inicializar_bd.py --actualizar` (MERGE: no duplica ni borra).

Opciones de `inicializar_bd.py`:

| Opción | Efecto |
|---|---|
| *(ninguna)* | Crea el esquema y carga los datos **solo si la base está vacía** |
| `--actualizar` | MERGE idempotente sobre una base con datos (no borra nada) |
| `--reemplazar` | Muestra el contenido actual, pide escribir `BORRAR` y recarga |
| `--solo-esquema` | Solo restricciones e índices |

> La aplicación **nunca borra datos automáticamente**. El vaciado total solo se hace desde *Administración* o desde `--reemplazar`, y exige escribir `BORRAR`.

## Pruebas

```powershell
python -m pytest -v
```

Las 65 pruebas se ejecutan **contra Neo4j real** y solo crean y borran datos marcados como `TEST-` / `@ejemplo.test`:

- `tests/test_integracion.py` (23): CRUD, vínculos, ofertas, postulaciones, rutas, recomendaciones con puntajes verificados a mano, analítica, perfil público, registro de empresas, idempotencia y salvaguardas.
- `tests/test_seguridad.py` (35): cifrado, política de contraseñas, validaciones, registro, inicio de sesión, bloqueo, sesiones, roles, permisos del reclutador, invitaciones y borrado selectivo de la demostración.
- `tests/test_ui.py` (7): cada pantalla con cada rol, registro e inicio de sesión desde los formularios y recuperación de la sesión desde la URL.

## Scripts y documentación

| Ruta | Descripción |
|---|---|
| `scripts/exportar_cypher.py` | Genera `cypher/01_esquema.cypher`, `02_datos_demo.cypher` y `03_consultas.cypher` desde el código |
| `scripts/generar_evidencias.py` | Ejecuta las consultas clave y las pruebas, y guarda los resultados reales en `docs/evidencias.md` |
| `scripts/diagrama_modelo.py` | Dibuja `docs/modelo_grafo.png` |
| `scripts/generar_docx.py` | Convierte el documento académico a Word (`docs/Documento_Academico_Orbita_final.docx`) |
| `docs/documento_academico.md` | Documento entregable (secciones 1-9 e investigación) |
| `docs/guia_demostracion.md` | Guion de demostración de 15 minutos |
| `docs/matriz_cumplimiento.md` | Matriz requisito · archivo · pantalla · Cypher · prueba · estado |

## Arquitectura

```
app.py                  Navegación Streamlit (barra lateral por secciones)
orbita/                  Capa de datos (sin dependencias de la interfaz)
  db.py                 Conexión (lee .env), leer()/escribir() parametrizados
  seguridad.py          Contraseñas, validaciones, inicio de sesión, bloqueo, sesiones y roles
  esquema.py            Restricciones, índices, conteos, borrado con salvaguarda
  usuarios.py           CRUD de usuarios + CONECTA_CON, TIENE_HABILIDAD, TRABAJA_EN, PARTICIPA_EN, POSTULA_A
  catalogo.py           CRUD de Empresa, Habilidad, Proyecto, Oferta + PUBLICA, REQUIERE, USA_TECNOLOGIA
  red.py                Contactos en común, similitud de Jaccard, rutas más cortas
  recomendaciones.py    Contactos, empleos, candidatos, colaboradores, proyectos relacionados
  analitica.py          Grado, PageRank, intermediación, comunidades (Louvain y componentes), demanda
  grafo_visual.py       Grafo interactivo (PyVis / vis.js)
  datos_demo.py         Datos de demostración deterministas y su exportación a Cypher
ui/                     Una página por módulo funcional
tests/                  Pruebas de integración y de interfaz
cypher/                 Scripts Cypher entregables
docs/                   Documento académico, evidencias, guía y matriz
```
