# Matriz de cumplimiento

Verificada el 2026-11-11 contra la instancia real de **Neo4j AuraDB** (Neo4j 5.27-aura).
Pruebas: `python -m pytest` → **65 aprobadas, 0 fallidas**. Pantallas en la barra lateral de `streamlit run app.py`.
Todas las consultas se pueden ver en la interfaz con el desplegable **"Ver consulta Cypher utilizada"** y están en `cypher/03_consultas.cypher`.

## A. "La aplicación debe permitir" (enunciado del profesor)

| # | Requisito exacto del documento | Archivo | Dónde comprobarlo en la interfaz | Consulta Cypher | Prueba realizada | Estado |
|---|---|---|---|---|---|---|
| 1 | Registrar, consultar, actualizar y eliminar (CRUD) usuarios con información personal y profesional | `orbita/usuarios.py`, `ui/usuarios_pg.py` | Crear cuenta y Mi perfil (cada usuario); Usuarios y cuentas → Directorio / Perfil / Registrar / Editar / Eliminar (administrador) | `Q_CREAR_USUARIO`, `Q_LISTAR_USUARIOS`, `Q_OBTENER_USUARIO`, `Q_ACTUALIZAR_USUARIO`, `Q_ELIMINAR_USUARIO` | `test_crud_usuario`, `test_unicidad_email`, `test_crear_usuario_valida_obligatorios`, `test_formulario_registra_usuario_en_neo4j` (escritura desde el formulario) | ✅ Funciona |
| 2 | Relacionar usuarios con otros usuarios mediante conexiones profesionales | `orbita/usuarios.py` | Mi red → Invitaciones / Mis conexiones / Descubrir personas; Usuarios y cuentas → Vínculos del perfil → Conexiones (administrador) | `Q_CONECTAR`, `Q_DESCONECTAR` | `test_conexiones` (simetría, sin duplicados, sin auto-conexión) | ✅ Funciona |
| 3 | Vincular usuarios con habilidades, empresas y proyectos | `orbita/usuarios.py` | Mi perfil → Habilidades / Experiencia / Proyectos; Proyectos; Usuarios y cuentas → Vínculos del perfil (administrador) | `Q_ASIGNAR_HABILIDAD`, `Q_VINCULAR_EMPRESA`, `Q_VINCULAR_PROYECTO` (+ sus inversas) | `test_vinculos_habilidad_empresa_proyecto` | ✅ Funciona |
| 4 | Registrar empresas y sus ofertas laborales que publican | `orbita/catalogo.py`, `ui/empresas_pg.py` | Mi empresa → Publicar oferta (reclutador); Mi perfil → Experiencia → Otra empresa; Empresas y ofertas (administrador) | `Q_CREAR_EMPRESA`, `Q_CREAR_OFERTA` (crea `PUBLICA` en la misma transacción), `Q_LISTAR_OFERTAS` | `test_empresas_ofertas_requisitos_postulacion` | ✅ Funciona |
| 5 | Relacionar ofertas laborales con las habilidades requeridas | `orbita/catalogo.py` | Mi empresa → Publicar oferta / Mis ofertas (reclutador); Empresas y ofertas → Requisitos de oferta (administrador) | `Q_CREAR_OFERTA`, `Q_AGREGAR_REQUISITO`, `Q_QUITAR_REQUISITO` | `test_empresas_ofertas_requisitos_postulacion` | ✅ Funciona |
| 6 | Permitir que un usuario se postule a una oferta | `orbita/usuarios.py` | Empleos → Postularme / Mis postulaciones; Mi empresa → Postulantes (reclutador) | `Q_POSTULAR`, `Q_ESTADO_POSTULACION`, `Q_RETIRAR_POSTULACION`, `Q_POSTULANTES` | `test_empresas_ofertas_requisitos_postulacion` (idempotente, rechaza ofertas cerradas) | ✅ Funciona |
| 7 | Consultar caminos y conexiones entre usuarios, empresas y oportunidades laborales | `orbita/red.py`, `ui/red_pg.py` | Rutas y conexiones → Ruta más corta (origen y destino de cualquier tipo, incluida Oferta) / Grado de separación | `Q_RUTA_PLANTILLA` (`shortestPath` / `allShortestPaths`), `Q_GRADO_SEPARACION` | `test_ruta_mas_corta_usuario_empresa_y_oferta` | ✅ Funciona |
| 8 | Generar recomendaciones de contactos, empleos o colaboradores a partir de la estructura del grafo | `orbita/recomendaciones.py`, `ui/recomendaciones_pg.py` | Recomendaciones → Contactos / Empleos / Colaboradores; Proyectos → Colaboradores sugeridos | `Q_RECOMENDAR_CONTACTOS`, `Q_RECOMENDAR_EMPLEOS`, `Q_RECOMENDAR_COLABORADORES_USUARIO`, `Q_RECOMENDAR_COLABORADORES_PROYECTO` | `test_recomendar_contactos`, `test_recomendar_empleos`, `test_colaboradores_y_proyectos_relacionados` (puntajes calculados a mano) | ✅ Funciona |
| 9 | Panel de analítica: usuarios más influyentes, comunidades detectadas y habilidades más demandadas | `orbita/analitica.py`, `ui/analitica_pg.py` | Analítica → Usuarios influyentes / Comunidades / Habilidades demandadas | `Q_CENTRALIDAD_GRADO`, `Q_ARISTAS_CONEXION` (+ PageRank, intermediación, Louvain y componentes en Python), `Q_HABILIDADES_DEMANDADAS` | `test_usuarios_influyentes`, `test_pagerank_suma_uno`, `test_comunidades` (modularidad > 0,3 y reproducible), `test_habilidades_mas_demandadas` | ✅ Funciona |

## B. Preguntas que el grafo debe responder

| # | Pregunta exacta | Archivo | Dónde comprobarlo | Consulta Cypher | Prueba | Estado |
|---|---|---|---|---|---|---|
| 1 | ¿Qué usuarios tienen habilidades similares? | `orbita/red.py` | Recomendaciones → Habilidades similares; Habilidades → Buscar profesionales | `Q_USUARIOS_SIMILARES`, `Q_PARES_SIMILARES` (Jaccard) | `test_usuarios_similares_jaccard` (2/3 y 1/3 exactos) | ✅ Funciona |
| 2 | ¿Qué contactos en común existen entre dos profesionales? | `orbita/red.py` | Rutas y conexiones → Contactos en común | `Q_CONTACTOS_EN_COMUN` | `test_contactos_en_comun` | ✅ Funciona |
| 3 | ¿Cuál es la ruta más corta entre un usuario y una empresa? | `orbita/red.py` | Rutas y conexiones → Ruta más corta (texto + grafo dibujado) | `Q_RUTA_USUARIO_EMPRESA`, `Q_RUTA_PLANTILLA` | `test_ruta_mas_corta_usuario_empresa_y_oferta` (3 saltos, nodos y relaciones exactos) | ✅ Funciona |
| 4 | ¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias? | `orbita/recomendaciones.py` | Recomendaciones → Candidatos para una oferta | `Q_RECOMENDAR_CANDIDATOS` (0,7·competencias + 0,3·red) | `test_recomendar_candidatos_formula` (47,0 y 38,0 verificados a mano) | ✅ Funciona |
| 5 | ¿Qué proyectos comparten tecnologías o miembros relacionados? | `orbita/recomendaciones.py` | Proyectos → Proyectos relacionados | `Q_PROYECTOS_RELACIONADOS`, `Q_PARES_PROYECTOS` | `test_colaboradores_y_proyectos_relacionados` | ✅ Funciona |
| 6 | ¿Qué habilidades son las más demandadas en las ofertas? | `orbita/analitica.py` | Analítica → Habilidades demandadas; Inicio | `Q_HABILIDADES_DEMANDADAS`, `Q_DEMANDA_POR_CATEGORIA` | `test_habilidades_mas_demandadas` (comparada con un conteo independiente) | ✅ Funciona |

## C. Modelo de grafo

| Requisito | Archivo | Dónde comprobarlo | Cypher | Prueba | Estado |
|---|---|---|---|---|---|
| Nodos Usuario, Empresa, Habilidad, Proyecto, Oferta | `orbita/datos_demo.py`, `orbita/esquema.py` | Administración → Nodos por etiqueta | `Q_CONTEO_NODOS` | `scripts/verificar_conexion.py`, `docs/evidencias.md` | ✅ Funciona |
| Relaciones CONECTA_CON, TRABAJA_EN, TIENE_HABILIDAD, PARTICIPA_EN, PUBLICA, REQUIERE, POSTULA_A | idem | Administración → Relaciones por tipo; Explorador del grafo | `Q_CONTEO_RELACIONES` | idem | ✅ Funciona |
| USA_TECNOLOGIA (Proyecto→Habilidad), añadida y aprobada | `orbita/catalogo.py` | Proyectos → Tecnologías y miembros | `Q_AGREGAR_TECNOLOGIA` | `test_crud_habilidad_y_proyecto` | ✅ Funciona |
| Restricciones de unicidad | `orbita/esquema.py`, `cypher/01_esquema.cypher` | Administración → Restricciones | `RESTRICCIONES` | `test_conexion_y_restricciones`, `test_unicidad_email` | ✅ Funciona |
| Consultas parametrizadas | todos los módulos `orbita/` | "Ver consulta Cypher" | 97 consultas con `$parámetros`; etiquetas y tipos con lista blanca | `EXPLAIN` de las 95 no plantilladas: 0 errores | ✅ Funciona |
| Datos de demostración amplios | `orbita/datos_demo.py`, `cypher/02_datos_demo.cypher` | Administración → Cargar datos | `CARGA` (MERGE) | `test_carga_demo_idempotente`; script `.cypher` ejecutado sin cambios | ✅ Funciona |
| Persistencia real en Neo4j (sin JSON/SQLite) | `orbita/db.py` | Todas | — | Todas las pruebas usan AuraDB | ✅ Funciona |
| Sin borrado automático; confirmación antes de borrar | `orbita/esquema.py`, `scripts/inicializar_bd.py`, `ui/admin_pg.py` | Administración → Zona peligrosa (exige escribir BORRAR) | `Q_BORRAR_TODO` | `test_borrado_requiere_confirmacion` | ✅ Funciona |

## D. Entregables

| Entregable | Archivo | Estado |
|---|---|---|
| Documento: explicación de las BD de grafos | `docs/documento_academico.md` §1 (y `.docx`) | ✅ Completo |
| Documento: modelo utilizado y diagrama | §3, §4, `docs/modelo_grafo.png` | ✅ Completo |
| Scripts de inicio de la BD | `cypher/01_esquema.cypher`, `cypher/02_datos_demo.cypher`, `scripts/inicializar_bd.py`, §5 | ✅ Completo y ejecutado |
| Script de las consultas utilizadas | `cypher/03_consultas.cypher`, §6 | ✅ Completo y validado |
| Componente de investigación (cuándo el grafo supera al relacional y cuándo no) | §7 | ✅ Completo |
| Justificación de Neo4j, evidencias, conclusiones | §2, §8, §9, `docs/evidencias.md` | ✅ Completo (faltan capturas de pantalla: ver pendientes) |
| Demostración ≤ 15 minutos | `docs/guia_demostracion.md` | ✅ Guion ensayado contra la base |

## Pendientes (requieren acción del estudiante)

1. **Capturas de pantalla** para la sección 8 del documento: el entorno de desarrollo no tiene navegador, por lo que no se pudieron tomar.
2. **Revisión visual en el navegador**: el renderizado se probó de forma automática (AppTest de Streamlit y servidor activo respondiendo), pero la apariencia final debe revisarse manualmente.

## F. Cuentas y seguridad (adicional)

| Requisito | Archivo | Dónde comprobarlo | Cypher | Prueba | Estado |
|---|---|---|---|---|---|
| Registro con validaciones | `orbita/seguridad.py`, `ui/auth_pg.py` | Pantalla de acceso → Crear cuenta | `Q_EMAIL_EXISTE`, `Q_REGISTRAR` | `test_registro_*`, `test_registro_desde_formulario_valida_y_crea_cuenta` | ✅ Funciona |
| Inicio de sesión, bloqueo y sesiones | `orbita/seguridad.py`, `ui/sesion.py` | Pantalla de acceso; recargar la página conserva la sesión | `Q_CREDENCIALES`, `Q_FALLO`, `Q_EXITO`, `Q_VALIDAR_SESION` | `test_bloqueo_tras_5_intentos`, `test_login_desde_app_y_restauracion_por_url` | ✅ Funciona |
| Roles y permisos | `orbita/seguridad.py`, `orbita/catalogo.py`, `app.py` | Menú según el rol; Administración → Usuarios y cuentas → Cuentas y roles | `Q_CAMBIAR_ROL`, `Q_PUEDE_PUBLICAR`, `Q_PUEDE_GESTIONAR_OFERTA` | `test_roles_y_permisos_admin`, `test_permisos_de_reclutador` | ✅ Funciona |
| Invitaciones de conexión | `orbita/usuarios.py`, `ui/mi_red_pg.py` | Mi red → Invitaciones / Descubrir personas | `Q_ENVIAR_INVITACION`, `Q_ACEPTAR_INVITACION` | `test_invitaciones` | ✅ Funciona |
| Borrado selectivo de los datos de demostración | `orbita/esquema.py`, `ui/admin_pg.py` | Administración → Base de datos | `Q_BORRAR_DEMO` | `test_borrar_solo_datos_demo` | ✅ Funciona |
