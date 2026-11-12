// Consultas Cypher de Órbita (extraídas automáticamente del código de la aplicación).
// Los valores con $ son parámetros enviados por el controlador de Neo4j (nunca concatenados).


// ============================================================================
// CRUD de usuarios y vínculos  (orbita.usuarios)
// ============================================================================

// ---- Q_CREAR_USUARIO
CREATE (u:Usuario {id: $id, fecha_registro: date()})
SET u += $props
RETURN u {.*, fecha_registro: toString(u.fecha_registro)} AS usuario;

// ---- Q_LISTAR_USUARIOS
MATCH (u:Usuario)
WHERE $texto = '' OR toLower(u.nombre) CONTAINS toLower($texto)
   OR toLower(coalesce(u.titular, '')) CONTAINS toLower($texto)
   OR toLower(coalesce(u.ciudad, '')) CONTAINS toLower($texto)
OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
WITH u, collect(e.nombre)[0] AS empresa_actual
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, u.ciudad AS ciudad,
       u.email AS email, u.anios_experiencia AS anios_experiencia, empresa_actual,
       coalesce(u.rol, 'profesional') AS rol, coalesce(u.activo, true) AS activo,
       u.password_hash IS NOT NULL AS tiene_password, toString(u.ultimo_acceso) AS ultimo_acceso,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS conexiones,
       COUNT { (u)-[:TIENE_HABILIDAD]->() } AS habilidades
ORDER BY nombre;

// ---- Q_OBTENER_USUARIO
MATCH (u:Usuario {id: $id})
RETURN u {.*, fecha_registro: toString(u.fecha_registro), actualizado: toString(u.actualizado),
          ultimo_acceso: toString(u.ultimo_acceso), rol: coalesce(u.rol, 'profesional')} AS usuario,
  [(u)-[r:TIENE_HABILIDAD]->(h:Habilidad) | {habilidad: h.nombre, categoria: h.categoria, nivel: r.nivel}] AS habilidades,
  [(u)-[r:TRABAJA_EN]->(e:Empresa) | {empresa_id: e.id, empresa: e.nombre, cargo: r.cargo, desde: r.desde, actual: r.actual}] AS empresas,
  [(u)-[r:PARTICIPA_EN]->(p:Proyecto) | {proyecto_id: p.id, proyecto: p.nombre, rol: r.rol}] AS proyectos,
  [(u)-[:CONECTA_CON]-(c:Usuario) | {id: c.id, nombre: c.nombre, titular: c.titular}] AS conexiones,
  [(u)-[r:POSTULA_A]->(o:Oferta)<-[:PUBLICA]-(e:Empresa) |
     {oferta_id: o.id, oferta: o.titulo, empresa: e.nombre, estado: r.estado, fecha: toString(r.fecha)}] AS postulaciones;

// ---- Q_ACTUALIZAR_USUARIO
MATCH (u:Usuario {id: $id})
SET u += $props, u.actualizado = datetime()
RETURN u {.*, fecha_registro: toString(u.fecha_registro), actualizado: toString(u.actualizado)} AS usuario;

// ---- Q_ELIMINAR_USUARIO
MATCH (u:Usuario {id: $id})
WITH u, COUNT { (u)--() } AS relaciones
DETACH DELETE u
RETURN relaciones;

// ---- Q_ASIGNAR_HABILIDAD
MATCH (u:Usuario {id: $usuario_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = coalesce($categoria, 'General')
MERGE (u)-[r:TIENE_HABILIDAD]->(h)
SET r.nivel = $nivel
RETURN u.nombre AS usuario, h.nombre AS habilidad, r.nivel AS nivel;

// ---- Q_QUITAR_HABILIDAD
MATCH (:Usuario {id: $usuario_id})-[r:TIENE_HABILIDAD]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_VINCULAR_EMPRESA
MATCH (u:Usuario {id: $usuario_id}), (e:Empresa {id: $empresa_id})
MERGE (u)-[r:TRABAJA_EN]->(e)
SET r.cargo = $cargo, r.desde = $desde, r.actual = $actual
RETURN u.nombre AS usuario, e.nombre AS empresa, r.cargo AS cargo;

// ---- Q_DESVINCULAR_EMPRESA
MATCH (:Usuario {id: $usuario_id})-[r:TRABAJA_EN]->(:Empresa {id: $empresa_id})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_VINCULAR_PROYECTO
MATCH (u:Usuario {id: $usuario_id}), (p:Proyecto {id: $proyecto_id})
MERGE (u)-[r:PARTICIPA_EN]->(p)
SET r.rol = $rol
RETURN u.nombre AS usuario, p.nombre AS proyecto, r.rol AS rol;

// ---- Q_DESVINCULAR_PROYECTO
MATCH (:Usuario {id: $usuario_id})-[r:PARTICIPA_EN]->(:Proyecto {id: $proyecto_id})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_CONECTAR
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
WHERE a <> b AND NOT (a)-[:CONECTA_CON]-(b)
CREATE (a)-[:CONECTA_CON {desde: date()}]->(b)
RETURN a.nombre AS origen, b.nombre AS destino;

// ---- Q_DESCONECTAR
MATCH (:Usuario {id: $a})-[r:CONECTA_CON]-(:Usuario {id: $b})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_POSTULAR
MATCH (u:Usuario {id: $usuario_id}), (o:Oferta {id: $oferta_id})
WHERE coalesce(o.activa, true)
MERGE (u)-[r:POSTULA_A]->(o)
  ON CREATE SET r.fecha = date(), r.estado = 'Enviada'
RETURN u.nombre AS usuario, o.titulo AS oferta, r.estado AS estado, toString(r.fecha) AS fecha;

// ---- Q_RETIRAR_POSTULACION
MATCH (:Usuario {id: $usuario_id})-[r:POSTULA_A]->(:Oferta {id: $oferta_id})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_ESTADO_POSTULACION
MATCH (:Usuario {id: $usuario_id})-[r:POSTULA_A]->(:Oferta {id: $oferta_id})
SET r.estado = $estado RETURN r.estado AS estado;

// ---- Q_INVITACION_INVERSA
RETURN EXISTS { (:Usuario {id: $b})-[:SOLICITA_CONEXION]->(:Usuario {id: $a}) } AS existe;

// ---- Q_ENVIAR_INVITACION
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
WHERE a <> b AND NOT (a)-[:CONECTA_CON]-(b)
MERGE (a)-[s:SOLICITA_CONEXION]->(b) ON CREATE SET s.fecha = datetime()
RETURN b.nombre AS destino;

// ---- Q_ACEPTAR_INVITACION
MATCH (emisor:Usuario {id: $emisor})-[s:SOLICITA_CONEXION]->(receptor:Usuario {id: $receptor})
DELETE s
WITH emisor, receptor
WHERE NOT (emisor)-[:CONECTA_CON]-(receptor)
CREATE (emisor)-[:CONECTA_CON {desde: date()}]->(receptor)
RETURN emisor.nombre AS nombre;

// ---- Q_BORRAR_INVITACION
MATCH (:Usuario {id: $emisor})-[s:SOLICITA_CONEXION]->(:Usuario {id: $receptor})
DELETE s RETURN count(*) AS eliminadas;

// ---- Q_INVITACIONES_RECIBIDAS
MATCH (e:Usuario)-[s:SOLICITA_CONEXION]->(:Usuario {id: $id})
RETURN e.id AS id, e.nombre AS nombre, e.titular AS titular, toString(date(s.fecha)) AS fecha,
       COUNT { (e)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(:Usuario {id: $id}) } AS en_comun
ORDER BY s.fecha DESC;

// ---- Q_INVITACIONES_ENVIADAS
MATCH (:Usuario {id: $id})-[s:SOLICITA_CONEXION]->(d:Usuario)
RETURN d.id AS id, d.nombre AS nombre, d.titular AS titular, toString(date(s.fecha)) AS fecha
ORDER BY s.fecha DESC;

// ---- Q_EMAIL_DE_OTRO
RETURN EXISTS { (u:Usuario {email: $email}) WHERE u.id <> $id } AS existe;

// ============================================================================
// Empresas, habilidades, proyectos y ofertas  (orbita.catalogo)
// ============================================================================

// ---- Q_CREAR_EMPRESA
CREATE (e:Empresa {id: $id}) SET e += $props
RETURN e {.*} AS empresa;

// ---- Q_LISTAR_EMPRESAS
MATCH (e:Empresa)
RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector, e.ciudad AS ciudad, e.tamano AS tamano,
       e.sitio_web AS sitio_web, e.descripcion AS descripcion,
       COUNT { (e)<-[:TRABAJA_EN {actual: true}]-(:Usuario) } AS empleados,
       COUNT { (e)-[:PUBLICA]->(:Oferta) } AS ofertas
ORDER BY nombre;

// ---- Q_ACTUALIZAR_EMPRESA
MATCH (e:Empresa {id: $id}) SET e += $props RETURN e {.*} AS empresa;

// ---- Q_ELIMINAR_EMPRESA
MATCH (e:Empresa {id: $id})
OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
WITH e, collect(o) AS ofertas
FOREACH (o IN ofertas | DETACH DELETE o)
DETACH DELETE e
RETURN size(ofertas) AS ofertas_eliminadas;

// ---- Q_CREAR_HABILIDAD
MERGE (h:Habilidad {nombre: $nombre})
SET h.categoria = $categoria
RETURN h {.*} AS habilidad;

// ---- Q_LISTAR_HABILIDADES
MATCH (h:Habilidad)
RETURN h.nombre AS nombre, h.categoria AS categoria,
       COUNT { (h)<-[:TIENE_HABILIDAD]-(:Usuario) } AS usuarios,
       COUNT { (h)<-[:REQUIERE]-(:Oferta) } AS ofertas,
       COUNT { (h)<-[:USA_TECNOLOGIA]-(:Proyecto) } AS proyectos
ORDER BY categoria, nombre;

// ---- Q_ACTUALIZAR_HABILIDAD
MATCH (h:Habilidad {nombre: $nombre})
SET h.nombre = $nuevo_nombre, h.categoria = $categoria
RETURN h {.*} AS habilidad;

// ---- Q_ELIMINAR_HABILIDAD
MATCH (h:Habilidad {nombre: $nombre})
WITH h, COUNT { (h)--() } AS relaciones
DETACH DELETE h RETURN relaciones;

// ---- Q_CREAR_PROYECTO
CREATE (p:Proyecto {id: $id}) SET p += $props
RETURN p {.*} AS proyecto;

// ---- Q_LISTAR_PROYECTOS
MATCH (p:Proyecto)
RETURN p.id AS id, p.nombre AS nombre, p.descripcion AS descripcion, p.estado AS estado, p.anio AS anio,
       [(p)-[:USA_TECNOLOGIA]->(h:Habilidad) | h.nombre] AS tecnologias,
       [(u:Usuario)-[:PARTICIPA_EN]->(p) | u.nombre] AS miembros
ORDER BY nombre;

// ---- Q_ACTUALIZAR_PROYECTO
MATCH (p:Proyecto {id: $id}) SET p += $props RETURN p {.*} AS proyecto;

// ---- Q_ELIMINAR_PROYECTO
MATCH (p:Proyecto {id: $id}) DETACH DELETE p RETURN count(*) AS eliminados;

// ---- Q_AGREGAR_TECNOLOGIA
MATCH (p:Proyecto {id: $proyecto_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (p)-[:USA_TECNOLOGIA]->(h)
RETURN p.nombre AS proyecto, h.nombre AS tecnologia;

// ---- Q_QUITAR_TECNOLOGIA
MATCH (:Proyecto {id: $proyecto_id})-[r:USA_TECNOLOGIA]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_CREAR_OFERTA
MATCH (e:Empresa {id: $empresa_id})
CREATE (e)-[:PUBLICA {fecha: date()}]->(o:Oferta {id: $id, fecha_publicacion: date(), activa: true})
SET o += $props
WITH e, o
UNWIND $requisitos AS req
MERGE (h:Habilidad {nombre: req.habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (o)-[r:REQUIERE]->(h)
SET r.nivel_minimo = req.nivel_minimo, r.obligatoria = req.obligatoria
RETURN o.id AS id, e.nombre AS empresa, count(h) AS habilidades;

// ---- Q_CREAR_OFERTA_SIN_REQ
MATCH (e:Empresa {id: $empresa_id})
CREATE (e)-[:PUBLICA {fecha: date()}]->(o:Oferta {id: $id, fecha_publicacion: date(), activa: true})
SET o += $props
RETURN o.id AS id, e.nombre AS empresa, 0 AS habilidades;

// ---- Q_LISTAR_OFERTAS
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE ($solo_activas = false OR o.activa) AND ($empresa_id = '' OR e.id = $empresa_id)
RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa, e.id AS empresa_id, o.ciudad AS ciudad,
       o.modalidad AS modalidad, o.nivel AS nivel, o.salario AS salario, o.activa AS activa,
       toString(o.fecha_publicacion) AS fecha_publicacion, o.descripcion AS descripcion,
       [(o)-[r:REQUIERE]->(h:Habilidad) | {habilidad: h.nombre, nivel_minimo: r.nivel_minimo, obligatoria: r.obligatoria}] AS requisitos,
       COUNT { (o)<-[:POSTULA_A]-(:Usuario) } AS postulantes
ORDER BY fecha_publicacion DESC, titulo;

// ---- Q_ACTUALIZAR_OFERTA
MATCH (o:Oferta {id: $id}) SET o += $props RETURN o {.*, fecha_publicacion: toString(o.fecha_publicacion)} AS oferta;

// ---- Q_ELIMINAR_OFERTA
MATCH (o:Oferta {id: $id}) DETACH DELETE o RETURN count(*) AS eliminadas;

// ---- Q_AGREGAR_REQUISITO
MATCH (o:Oferta {id: $oferta_id})
MERGE (h:Habilidad {nombre: $habilidad})
  ON CREATE SET h.categoria = 'General'
MERGE (o)-[r:REQUIERE]->(h)
SET r.nivel_minimo = $nivel_minimo, r.obligatoria = $obligatoria
RETURN o.titulo AS oferta, h.nombre AS habilidad;

// ---- Q_QUITAR_REQUISITO
MATCH (:Oferta {id: $oferta_id})-[r:REQUIERE]->(:Habilidad {nombre: $habilidad})
DELETE r RETURN count(*) AS eliminadas;

// ---- Q_POSTULANTES
MATCH (u:Usuario)-[r:POSTULA_A]->(o:Oferta {id: $oferta_id})
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, r.estado AS estado, toString(r.fecha) AS fecha,
       size([(o)-[:REQUIERE]->(h)<-[:TIENE_HABILIDAD]-(u) | h]) AS habilidades_cumplidas,
       COUNT { (o)-[:REQUIERE]->() } AS habilidades_requeridas
ORDER BY habilidades_cumplidas DESC, nombre;

// ---- Q_EMPRESAS_ACTUALES
MATCH (:Usuario {id: $id})-[:TRABAJA_EN {actual: true}]->(e:Empresa)
RETURN e.id AS id, e.nombre AS nombre ORDER BY nombre;

// ---- Q_PUEDE_PUBLICAR
MATCH (u:Usuario {id: $actor})
RETURN coalesce(u.activo, true) AND (u.rol = 'admin' OR (u.rol = 'reclutador'
       AND EXISTS { (u)-[:TRABAJA_EN {actual: true}]->(:Empresa {id: $empresa_id}) })) AS puede;

// ---- Q_PUEDE_GESTIONAR_OFERTA
MATCH (u:Usuario {id: $actor})
RETURN coalesce(u.activo, true) AND (u.rol = 'admin' OR (u.rol = 'reclutador'
       AND EXISTS { (u)-[:TRABAJA_EN {actual: true}]->(:Empresa)-[:PUBLICA]->(:Oferta {id: $oferta_id}) })) AS puede;

// ---- Q_ES_MIEMBRO
RETURN EXISTS { (:Usuario {id: $u})-[:PARTICIPA_EN]->(:Proyecto {id: $p}) } AS miembro;

// ---- Q_BUSCAR_OFERTAS
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE coalesce(o.activa, true)
  AND ($texto = '' OR toLower(o.titulo) CONTAINS toLower($texto) OR toLower(e.nombre) CONTAINS toLower($texto))
  AND ($modalidad = '' OR o.modalidad = $modalidad)
  AND ($ciudad = '' OR o.ciudad = $ciudad)
  AND (size($habilidades) = 0 OR ALL(h IN $habilidades WHERE EXISTS { (o)-[:REQUIERE]->(:Habilidad {nombre: h}) }))
OPTIONAL MATCH (o)-[r:REQUIERE]->(h:Habilidad)
OPTIONAL MATCH (:Usuario {id: $usuario_id})-[t:TIENE_HABILIDAD]->(h)
WITH e, o, collect({habilidad: h.nombre, obligatoria: r.obligatoria, nivel_minimo: r.nivel_minimo, tengo: t IS NOT NULL}) AS requisitos
RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa, o.ciudad AS ciudad, o.modalidad AS modalidad, o.nivel AS nivel,
       o.salario AS salario, toString(o.fecha_publicacion) AS fecha_publicacion, o.descripcion AS descripcion,
       [x IN requisitos WHERE x.habilidad IS NOT NULL] AS requisitos,
       EXISTS { (:Usuario {id: $usuario_id})-[:POSTULA_A]->(o) } AS postulado,
       COUNT { (o)<-[:POSTULA_A]-() } AS postulantes
ORDER BY o.fecha_publicacion DESC;

// ============================================================================
// Red: contactos en común, similitud y rutas más cortas  (orbita.red)
// ============================================================================

// ---- Q_CONTACTOS_EN_COMUN
MATCH (a:Usuario {id: $a})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b:Usuario {id: $b})
WHERE a <> b
RETURN DISTINCT c.id AS id, c.nombre AS nombre, c.titular AS titular, c.ciudad AS ciudad,
       COUNT { (c)-[:CONECTA_CON]-(:Usuario) } AS conexiones
ORDER BY conexiones DESC, nombre;

// ---- Q_ESTAN_CONECTADOS
RETURN EXISTS { (:Usuario {id: $a})-[:CONECTA_CON]-(:Usuario {id: $b}) } AS conectados;

// ---- Q_USUARIOS_SIMILARES
MATCH (u:Usuario {id: $id})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(o:Usuario)
WITH u, o, collect(h.nombre) AS compartidas
WITH u, o, compartidas,
     COUNT { (u)-[:TIENE_HABILIDAD]->() } AS nu,
     COUNT { (o)-[:TIENE_HABILIDAD]->() } AS no
RETURN o.id AS id, o.nombre AS nombre, o.titular AS titular, compartidas,
       size(compartidas) AS en_comun,
       round(toFloat(size(compartidas)) / (nu + no - size(compartidas)), 3) AS jaccard,
       EXISTS { (u)-[:CONECTA_CON]-(o) } AS ya_conectados
ORDER BY jaccard DESC, en_comun DESC, nombre
LIMIT $limite;

// ---- Q_PARES_SIMILARES
MATCH (a:Usuario)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(b:Usuario)
WHERE a.id < b.id
WITH a, b, collect(h.nombre) AS compartidas
WITH a, b, compartidas,
     COUNT { (a)-[:TIENE_HABILIDAD]->() } AS na,
     COUNT { (b)-[:TIENE_HABILIDAD]->() } AS nb
WHERE size(compartidas) >= $minimo
RETURN a.nombre AS usuario_a, b.nombre AS usuario_b, compartidas, size(compartidas) AS en_comun,
       round(toFloat(size(compartidas)) / (na + nb - size(compartidas)), 3) AS jaccard
ORDER BY jaccard DESC, en_comun DESC
LIMIT $limite;

// ---- Q_USUARIOS_CON_HABILIDAD
MATCH (u:Usuario)-[r:TIENE_HABILIDAD]->(h:Habilidad)
WHERE h.nombre IN $habilidades
WITH u, collect(h.nombre) AS tiene, avg(r.nivel) AS nivel_promedio
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, tiene, size(tiene) AS coincidencias,
       round(nivel_promedio, 2) AS nivel_promedio
ORDER BY coincidencias DESC, nivel_promedio DESC;

// ---- Q_RUTA_PLANTILLA
MATCH (a:{eo} {{{ko}: $origen}}), (b:{ed} {{{kd}: $destino}})
MATCH p = {funcion}((a)-[:{tipos}*..{max}]-(b))
RETURN [n IN nodes(p) | {{etiqueta: labels(n)[0], nombre: coalesce(n.nombre, n.titulo), id: coalesce(n.id, n.nombre)}}] AS nodos,
       [r IN relationships(p) | type(r)] AS relaciones,
       length(p) AS saltos
LIMIT $limite;

// ---- Q_RUTA_USUARIO_EMPRESA
MATCH (a:Usuario {id: $origen}), (b:Empresa {id: $destino})
MATCH p = shortestPath((a)-[:CONECTA_CON|TRABAJA_EN*..8]-(b))
RETURN [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS nodos, [r IN relationships(p) | type(r)] AS relaciones,
       length(p) AS saltos;

// ---- Q_GRADO_SEPARACION
MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
OPTIONAL MATCH p = shortestPath((a)-[:CONECTA_CON*..10]-(b))
RETURN CASE WHEN p IS NULL THEN null ELSE length(p) END AS grado,
       [n IN coalesce(nodes(p), []) | n.nombre] AS ruta;

// ============================================================================
// Recomendaciones  (orbita.recomendaciones)
// ============================================================================

// ---- Q_RECOMENDAR_CONTACTOS
MATCH (u:Usuario {id: $id})
MATCH (o:Usuario)
WHERE o <> u AND NOT (u)-[:CONECTA_CON]-(o)
WITH u, o,
     COLLECT { MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(o) RETURN DISTINCT c.nombre } AS comunes,
     COLLECT { MATCH (u)-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(o) RETURN h.nombre } AS habilidades,
     COLLECT { MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)<-[:TRABAJA_EN {actual: true}]-(o) RETURN e.nombre } AS empresas,
     COLLECT { MATCH (u)-[:PARTICIPA_EN]->(p:Proyecto)<-[:PARTICIPA_EN]-(o) RETURN p.nombre } AS proyectos
WHERE size(comunes) > 0 OR size(habilidades) > 0
WITH o, comunes, habilidades, empresas, proyectos,
     3 * size(comunes) + 2 * size(habilidades) + 2 * size(empresas) + 2 * size(proyectos) AS puntaje
RETURN o.id AS id, o.nombre AS nombre, o.titular AS titular, puntaje,
       size(comunes) AS contactos_en_comun, comunes, habilidades AS habilidades_compartidas,
       empresas AS empresa_compartida, proyectos AS proyectos_compartidos
ORDER BY puntaje DESC, nombre
LIMIT $limite;

// ---- Q_RECOMENDAR_EMPLEOS
MATCH (u:Usuario {id: $id})
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE coalesce(o.activa, true) AND NOT (u)-[:POSTULA_A]->(o) AND NOT (u)-[:TRABAJA_EN {actual: true}]->(e)

MATCH (o)-[req:REQUIERE]->(h:Habilidad)
OPTIONAL MATCH (u)-[th:TIENE_HABILIDAD]->(h)
WITH e, o, u,
     CASE WHEN coalesce(req.obligatoria, true) THEN 2.0 ELSE 1.0 END AS peso,
     coalesce(req.nivel_minimo, 1) AS minimo, th, h
WITH e, o, u, sum(peso) AS max_puntos,
     sum(CASE WHEN th IS NULL THEN 0.0 WHEN th.nivel >= minimo THEN peso ELSE peso * 0.5 END) AS puntos,
     collect(CASE WHEN th IS NOT NULL THEN h.nombre END) AS cumple,
     collect(CASE WHEN th IS NULL THEN h.nombre END) AS faltan
WHERE puntos > 0
WITH e, o, u, puntos / max_puntos AS cobertura, cumple, faltan,
     COLLECT { MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:TRABAJA_EN {actual: true}]->(e) RETURN DISTINCT c.nombre } AS directos,
     COLLECT { MATCH (u)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(x:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
               WHERE x <> u AND NOT (u)-[:CONECTA_CON]-(x) RETURN DISTINCT x.nombre } AS segundo_grado
WITH e, o, u, cobertura, cumple, faltan, directos, segundo_grado,
     CASE WHEN (size(directos) + 0.5 * size(segundo_grado)) / 3.0 > 1 THEN 1.0
          ELSE (size(directos) + 0.5 * size(segundo_grado)) / 3.0 END AS red

RETURN o.id AS oferta_id, o.titulo AS oferta, e.nombre AS empresa, o.ciudad AS ciudad, o.modalidad AS modalidad,
       round(100 * (0.7 * cobertura + 0.3 * red), 1) AS puntaje,
       round(100 * cobertura, 1) AS cobertura_pct, cumple, faltan,
       directos AS contactos_en_empresa, size(segundo_grado) AS contactos_2do_grado
ORDER BY puntaje DESC, oferta
LIMIT $limite;

// ---- Q_RECOMENDAR_CANDIDATOS
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $oferta_id})
MATCH (u:Usuario)
WHERE NOT (u)-[:TRABAJA_EN {actual: true}]->(e)

MATCH (o)-[req:REQUIERE]->(h:Habilidad)
OPTIONAL MATCH (u)-[th:TIENE_HABILIDAD]->(h)
WITH e, o, u,
     CASE WHEN coalesce(req.obligatoria, true) THEN 2.0 ELSE 1.0 END AS peso,
     coalesce(req.nivel_minimo, 1) AS minimo, th, h
WITH e, o, u, sum(peso) AS max_puntos,
     sum(CASE WHEN th IS NULL THEN 0.0 WHEN th.nivel >= minimo THEN peso ELSE peso * 0.5 END) AS puntos,
     collect(CASE WHEN th IS NOT NULL THEN h.nombre END) AS cumple,
     collect(CASE WHEN th IS NULL THEN h.nombre END) AS faltan
WHERE puntos > 0
WITH e, o, u, puntos / max_puntos AS cobertura, cumple, faltan,
     COLLECT { MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:TRABAJA_EN {actual: true}]->(e) RETURN DISTINCT c.nombre } AS directos,
     COLLECT { MATCH (u)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(x:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
               WHERE x <> u AND NOT (u)-[:CONECTA_CON]-(x) RETURN DISTINCT x.nombre } AS segundo_grado
WITH e, o, u, cobertura, cumple, faltan, directos, segundo_grado,
     CASE WHEN (size(directos) + 0.5 * size(segundo_grado)) / 3.0 > 1 THEN 1.0
          ELSE (size(directos) + 0.5 * size(segundo_grado)) / 3.0 END AS red

RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular,
       round(100 * (0.7 * cobertura + 0.3 * red), 1) AS puntaje,
       round(100 * cobertura, 1) AS cobertura_pct, cumple, faltan,
       directos AS contactos_en_empresa, size(segundo_grado) AS contactos_2do_grado,
       EXISTS { (u)-[:POSTULA_A]->(o) } AS ya_postulado
ORDER BY puntaje DESC, nombre
LIMIT $limite;

// ---- Q_RECOMENDAR_COLABORADORES_USUARIO
MATCH (u:Usuario {id: $id})
WITH u, COLLECT { MATCH (u)-[:PARTICIPA_EN]->(:Proyecto)-[:USA_TECNOLOGIA]->(t:Habilidad) RETURN DISTINCT t } AS tecnologias
MATCH (c:Usuario)-[:TIENE_HABILIDAD]->(h:Habilidad)
WHERE c <> u AND h IN tecnologias
  AND NOT EXISTS { (u)-[:PARTICIPA_EN]->(:Proyecto)<-[:PARTICIPA_EN]-(c) }
WITH u, c, collect(DISTINCT h.nombre) AS aporta
WITH u, c, aporta,
     EXISTS { (u)-[:CONECTA_CON]-(c) } AS conectado,
     COUNT { MATCH (u)-[:CONECTA_CON]-(x:Usuario)-[:CONECTA_CON]-(c) RETURN DISTINCT x } AS comunes
RETURN c.id AS id, c.nombre AS nombre, c.titular AS titular,
       2 * size(aporta) + CASE WHEN conectado THEN 3 ELSE 0 END + comunes AS puntaje,
       aporta AS tecnologias_que_aporta, conectado, comunes AS contactos_en_comun
ORDER BY puntaje DESC, nombre
LIMIT $limite;

// ---- Q_RECOMENDAR_COLABORADORES_PROYECTO
MATCH (p:Proyecto {id: $proyecto_id})-[:USA_TECNOLOGIA]->(t:Habilidad)<-[th:TIENE_HABILIDAD]-(c:Usuario)
WHERE NOT (c)-[:PARTICIPA_EN]->(p)
WITH p, c, collect(t.nombre) AS domina, avg(th.nivel) AS nivel
WITH p, c, domina, nivel,
     COLLECT { MATCH (c)-[:CONECTA_CON]-(m:Usuario)-[:PARTICIPA_EN]->(p) RETURN DISTINCT m.nombre } AS miembros_conocidos
RETURN c.id AS id, c.nombre AS nombre, c.titular AS titular,
       round(2 * size(domina) + 1.5 * size(miembros_conocidos), 1) AS puntaje,
       domina AS tecnologias, round(nivel, 1) AS nivel_promedio, miembros_conocidos
ORDER BY puntaje DESC, nivel_promedio DESC, nombre
LIMIT $limite;

// ---- Q_PROYECTOS_RELACIONADOS
MATCH (p:Proyecto {id: $proyecto_id}), (q:Proyecto)
WHERE q <> p
WITH p, q,
     COLLECT { MATCH (p)-[:USA_TECNOLOGIA]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(q) RETURN h.nombre } AS tecnologias,
     COLLECT { MATCH (p)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(q) RETURN m.nombre } AS miembros,
     COLLECT { MATCH (p)<-[:PARTICIPA_EN]-(m1:Usuario)-[:CONECTA_CON]-(m2:Usuario)-[:PARTICIPA_EN]->(q)
               WHERE m1 <> m2 RETURN DISTINCT m1.nombre + ' ↔ ' + m2.nombre } AS conectados
WHERE size(tecnologias) + size(miembros) + size(conectados) > 0
RETURN q.id AS id, q.nombre AS proyecto,
       2 * size(tecnologias) + 3 * size(miembros) + size(conectados) AS puntaje,
       tecnologias AS tecnologias_compartidas, miembros AS miembros_compartidos,
       conectados AS miembros_relacionados
ORDER BY puntaje DESC, proyecto;

// ---- Q_PARES_PROYECTOS
MATCH (p:Proyecto), (q:Proyecto)
WHERE p.id < q.id
WITH p, q,
     COLLECT { MATCH (p)-[:USA_TECNOLOGIA]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(q) RETURN h.nombre } AS tecnologias,
     COLLECT { MATCH (p)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(q) RETURN m.nombre } AS miembros,
     COUNT { MATCH (p)<-[:PARTICIPA_EN]-(m1:Usuario)-[:CONECTA_CON]-(m2:Usuario)-[:PARTICIPA_EN]->(q)
             WHERE m1 <> m2 RETURN DISTINCT m1, m2 } AS pares_conectados
WHERE size(tecnologias) + size(miembros) > 0
RETURN p.nombre AS proyecto_a, q.nombre AS proyecto_b, tecnologias AS tecnologias_compartidas,
       miembros AS miembros_compartidos, pares_conectados,
       2 * size(tecnologias) + 3 * size(miembros) + pares_conectados AS puntaje
ORDER BY puntaje DESC
LIMIT $limite;

// ============================================================================
// Analítica  (orbita.analitica)
// ============================================================================

// ---- Q_CENTRALIDAD_GRADO
MATCH (u:Usuario)
OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, collect(e.nombre)[0] AS empresa,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS conexiones,
       COUNT { (u)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(x:Usuario) WHERE x <> u } AS alcance_2_saltos,
       COUNT { (u)-[:PARTICIPA_EN]->(:Proyecto) } AS proyectos
ORDER BY conexiones DESC, nombre;

// ---- Q_ARISTAS_CONEXION
MATCH (a:Usuario)-[:CONECTA_CON]->(b:Usuario)
RETURN a.id AS origen, b.id AS destino;

// ---- Q_NODOS_USUARIO
MATCH (u:Usuario) RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, u.ciudad AS ciudad;

// ---- Q_GUARDAR_COMUNIDAD
UNWIND $filas AS fila
MATCH (u:Usuario {id: fila.id})
SET u.comunidad = fila.comunidad
RETURN count(u) AS actualizados;

// ---- Q_HABILIDADES_DEMANDADAS
MATCH (o:Oferta)-[r:REQUIERE]->(h:Habilidad)
WHERE ($solo_activas = false OR coalesce(o.activa, true))
WITH h, count(DISTINCT o) AS ofertas, sum(CASE WHEN r.obligatoria THEN 1 ELSE 0 END) AS obligatoria_en
RETURN h.nombre AS habilidad, h.categoria AS categoria, ofertas, obligatoria_en,
       COUNT { (h)<-[:TIENE_HABILIDAD]-(:Usuario) } AS profesionales_que_la_tienen,
       COUNT { (h)<-[:USA_TECNOLOGIA]-(:Proyecto) } AS proyectos_que_la_usan
ORDER BY ofertas DESC, obligatoria_en DESC, habilidad
LIMIT $limite;

// ---- Q_DEMANDA_POR_CATEGORIA
MATCH (o:Oferta)-[:REQUIERE]->(h:Habilidad)
WHERE coalesce(o.activa, true)
RETURN h.categoria AS categoria, count(*) AS requerimientos, count(DISTINCT o) AS ofertas
ORDER BY requerimientos DESC;

// ---- Q_EMPRESAS_ACTIVAS
MATCH (e:Empresa)
RETURN e.nombre AS empresa, e.sector AS sector,
       COUNT { (e)-[:PUBLICA]->(:Oferta) } AS ofertas,
       COUNT { (e)-[:PUBLICA]->(:Oferta)<-[:POSTULA_A]-(:Usuario) } AS postulaciones,
       COUNT { (e)<-[:TRABAJA_EN {actual: true}]-(:Usuario) } AS empleados
ORDER BY postulaciones DESC, ofertas DESC;

// ---- Q_RESUMEN
RETURN COUNT { (:Usuario) } AS usuarios, COUNT { (:Empresa) } AS empresas,
       COUNT { (:Habilidad) } AS habilidades, COUNT { (:Proyecto) } AS proyectos,
       COUNT { (o:Oferta) WHERE coalesce(o.activa, true) } AS ofertas_activas,
       COUNT { ()-[:CONECTA_CON]->() } AS conexiones,
       COUNT { ()-[:POSTULA_A]->() } AS postulaciones,
       COUNT { ()-[]->() } AS relaciones;

// ---- Q_USUARIOS_POR_CIUDAD
MATCH (u:Usuario) RETURN coalesce(u.ciudad, 'Sin ciudad') AS ciudad, count(*) AS usuarios ORDER BY usuarios DESC;

// ============================================================================
// Visualización  (orbita.grafo_visual)
// ============================================================================

// ---- Q_SUBGRAFO
MATCH (a)-[r]->(b)
WHERE type(r) IN $tipos AND labels(a)[0] IN $etiquetas AND labels(b)[0] IN $etiquetas
RETURN {id: elementId(a), etiqueta: labels(a)[0], nombre: coalesce(a.nombre, a.titulo),
  clave: coalesce(a.id, a.nombre), detalle: coalesce(a.titular, a.sector, a.categoria, a.estado, a.modalidad, '')} AS a, type(r) AS tipo, {id: elementId(b), etiqueta: labels(b)[0], nombre: coalesce(b.nombre, b.titulo),
  clave: coalesce(b.id, b.nombre), detalle: coalesce(b.titular, b.sector, b.categoria, b.estado, b.modalidad, '')} AS b
LIMIT $limite;

// ---- Q_EGO
MATCH (centro {%(clave)s: $clave}) WHERE $etiqueta IN labels(centro)
MATCH (centro)-[*1..%(saltos)d]-(x)
WITH centro, collect(DISTINCT x)[..$max_nodos] + [centro] AS nodos
UNWIND nodos AS a
MATCH (a)-[r]->(b) WHERE b IN nodos
RETURN %(na)s AS a, type(r) AS tipo, %(nb)s AS b;

// ============================================================================
// Administración  (orbita.esquema)
// ============================================================================

// ---- Q_ORIGEN_DATOS
UNWIND ['Usuario','Empresa','Habilidad','Proyecto','Oferta'] AS etiqueta
CALL (etiqueta) {
  MATCH (n) WHERE etiqueta IN labels(n)
  RETURN sum(CASE WHEN n.demo IS NOT NULL THEN 1 ELSE 0 END) AS demo,
         sum(CASE WHEN n.demo IS NULL THEN 1 ELSE 0 END) AS reales
}
RETURN etiqueta, demo, reales;

// ---- Q_BORRAR_DEMO
MATCH (n {demo: $lote})
WHERE NOT ((n:Habilidad OR n:Empresa) AND EXISTS { (n)--(m) WHERE m.demo IS NULL OR m.demo <> $lote })
WITH collect(n) AS nodos
FOREACH (n IN nodos | DETACH DELETE n)
RETURN size(nodos) AS eliminados;

// ---- Q_CONSERVAR_RESTANTES
MATCH (n {demo: $lote}) REMOVE n.demo RETURN count(n) AS conservados;

// ---- Q_CONTEO_NODOS
UNWIND ['Usuario','Empresa','Habilidad','Proyecto','Oferta'] AS etiqueta
CALL (etiqueta) {
  MATCH (n) WHERE etiqueta IN labels(n) RETURN count(n) AS total
}
RETURN etiqueta, total;

// ---- Q_CONTEO_RELACIONES
MATCH ()-[r]->() RETURN type(r) AS tipo, count(r) AS total ORDER BY total DESC;

// ---- Q_TOTAL
MATCH (n) RETURN count(n) AS nodos;

// ---- Q_BORRAR_TODO
MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS;

// ============================================================================
// Autenticación, sesiones y roles  (orbita.seguridad)
// ============================================================================

// ---- Q_EMAIL_EXISTE
RETURN EXISTS { (:Usuario {email: $email}) } AS existe;

// ---- Q_REGISTRAR
CREATE (u:Usuario {id: $id, fecha_registro: date(), rol: 'profesional', activo: true,
                   password_hash: $hash, intentos_fallidos: 0})
SET u += $props
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, u.rol AS rol;

// ---- Q_CREDENCIALES
MATCH (u:Usuario {email: $email})
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, coalesce(u.rol, 'profesional') AS rol,
       u.password_hash AS hash, coalesce(u.activo, true) AS activo,
       coalesce(u.bloqueado_hasta > datetime(), false) AS bloqueado,
       CASE WHEN u.bloqueado_hasta > datetime()
            THEN duration.inSeconds(datetime(), u.bloqueado_hasta).seconds ELSE 0 END AS segundos_restantes;

// ---- Q_FALLO
MATCH (u:Usuario {id: $id})
SET u.intentos_fallidos = coalesce(u.intentos_fallidos, 0) + 1
WITH u, u.intentos_fallidos >= $max AS bloquear
FOREACH (_ IN CASE WHEN bloquear THEN [1] ELSE [] END |
  SET u.bloqueado_hasta = datetime() + duration({minutes: $minutos}), u.intentos_fallidos = 0)
RETURN bloquear, u.intentos_fallidos AS intentos;

// ---- Q_EXITO
MATCH (u:Usuario {id: $id})
SET u.intentos_fallidos = 0, u.bloqueado_hasta = null, u.ultimo_acceso = datetime(),
    u.sesion_hash = $sesion_hash, u.sesion_expira = datetime() + duration({hours: $horas});

// ---- Q_VALIDAR_SESION
MATCH (u:Usuario {sesion_hash: $sesion_hash})
WHERE u.sesion_expira > datetime() AND coalesce(u.activo, true)
RETURN u.id AS id, u.nombre AS nombre, u.email AS email, coalesce(u.rol, 'profesional') AS rol;

// ---- Q_CERRAR_SESION
MATCH (u:Usuario {id: $id}) REMOVE u.sesion_hash, u.sesion_expira;

// ---- Q_HASH_ACTUAL
MATCH (u:Usuario {id: $id}) RETURN u.password_hash AS hash;

// ---- Q_FIJAR_PASSWORD
MATCH (u:Usuario {id: $id})
SET u.password_hash = $hash, u.intentos_fallidos = 0, u.bloqueado_hasta = null
REMOVE u.sesion_hash, u.sesion_expira
RETURN u.id AS id;

// ---- Q_ES_ADMIN
MATCH (u:Usuario {id: $id}) RETURN coalesce(u.rol, '') = 'admin' AND coalesce(u.activo, true) AS es_admin;

// ---- Q_CAMBIAR_ROL
MATCH (u:Usuario {id: $id}) SET u.rol = $rol RETURN u.rol AS rol;

// ---- Q_CONTAR_ADMINS
MATCH (u:Usuario {rol: 'admin'}) WHERE coalesce(u.activo, true) RETURN count(u) AS n;

// ---- Q_ACTIVAR
MATCH (u:Usuario {id: $id}) SET u.activo = $activo
FOREACH (_ IN CASE WHEN $activo THEN [] ELSE [1] END | REMOVE u.sesion_hash, u.sesion_expira)
RETURN u.activo AS activo;

// ---- Q_RUTA (ejemplo generado: usuario → empresa por la red profesional)
MATCH (a:Usuario {id: $origen}), (b:Empresa {id: $destino})
MATCH p = shortestPath((a)-[:CONECTA_CON|TRABAJA_EN*..8]-(b))
RETURN [n IN nodes(p) | {etiqueta: labels(n)[0], nombre: coalesce(n.nombre, n.titulo), id: coalesce(n.id, n.nombre)}] AS nodos,
       [r IN relationships(p) | type(r)] AS relaciones,
       length(p) AS saltos
LIMIT $limite;
