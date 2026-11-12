"""Motores de recomendación basados en la estructura del grafo.

Todos los puntajes son deterministas (mismos datos => mismo resultado) y se calculan en Cypher.

1. Contactos   puntaje = 3·contactos_en_común + 2·habilidades_compartidas
                         + 2·[misma empresa actual] + 2·proyectos_compartidos
   Solo usuarios aún no conectados y con al menos un contacto o habilidad en común.

2. Empleos     cobertura = Σ pesos de habilidades requeridas cubiertas / Σ pesos requeridos
                 peso = 2 si la habilidad es obligatoria, 1 si es deseable;
                 si el usuario tiene la habilidad con nivel < nivel_minimo cuenta la mitad.
               red = min(1, (contactos directos en la empresa + 0.5·contactos de 2.º grado) / 3)
               puntaje = 100 · (0.7·cobertura + 0.3·red)
   Excluye ofertas cerradas, ya postuladas y de la empresa donde ya trabaja.

3. Candidatos  misma fórmula que (2), vista desde la oferta: todos los usuarios que no
               trabajan actualmente en la empresa, con cobertura > 0.

4. Colaboradores (para un usuario)
               T = tecnologías de los proyectos del usuario.
               puntaje = 2·|habilidades del candidato ∩ T| + 3·[conectado] + 1·contactos_en_común
   Excluye a quienes ya comparten proyecto con el usuario.

5. Colaboradores (para un proyecto)
               puntaje = 2·tecnologías del proyecto que domina + 1.5·miembros con los que está conectado

6. Proyectos relacionados
               puntaje = 2·tecnologías compartidas + 3·miembros compartidos + 1·pares de miembros conectados
"""
from __future__ import annotations

from .db import leer

Q_RECOMENDAR_CONTACTOS = """
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
LIMIT $limite
"""

# Fragmento común: cobertura de habilidades + cercanía en la red respecto a la empresa
_COBERTURA_Y_RED = """
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
"""

Q_RECOMENDAR_EMPLEOS = """
MATCH (u:Usuario {id: $id})
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
WHERE coalesce(o.activa, true) AND NOT (u)-[:POSTULA_A]->(o) AND NOT (u)-[:TRABAJA_EN {actual: true}]->(e)
""" + _COBERTURA_Y_RED + """
RETURN o.id AS oferta_id, o.titulo AS oferta, e.nombre AS empresa, o.ciudad AS ciudad, o.modalidad AS modalidad,
       round(100 * (0.7 * cobertura + 0.3 * red), 1) AS puntaje,
       round(100 * cobertura, 1) AS cobertura_pct, cumple, faltan,
       directos AS contactos_en_empresa, size(segundo_grado) AS contactos_2do_grado
ORDER BY puntaje DESC, oferta
LIMIT $limite
"""

Q_RECOMENDAR_CANDIDATOS = """
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $oferta_id})
MATCH (u:Usuario)
WHERE NOT (u)-[:TRABAJA_EN {actual: true}]->(e)
""" + _COBERTURA_Y_RED + """
RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular,
       round(100 * (0.7 * cobertura + 0.3 * red), 1) AS puntaje,
       round(100 * cobertura, 1) AS cobertura_pct, cumple, faltan,
       directos AS contactos_en_empresa, size(segundo_grado) AS contactos_2do_grado,
       EXISTS { (u)-[:POSTULA_A]->(o) } AS ya_postulado
ORDER BY puntaje DESC, nombre
LIMIT $limite
"""

Q_RECOMENDAR_COLABORADORES_USUARIO = """
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
LIMIT $limite
"""

Q_RECOMENDAR_COLABORADORES_PROYECTO = """
MATCH (p:Proyecto {id: $proyecto_id})-[:USA_TECNOLOGIA]->(t:Habilidad)<-[th:TIENE_HABILIDAD]-(c:Usuario)
WHERE NOT (c)-[:PARTICIPA_EN]->(p)
WITH p, c, collect(t.nombre) AS domina, avg(th.nivel) AS nivel
WITH p, c, domina, nivel,
     COLLECT { MATCH (c)-[:CONECTA_CON]-(m:Usuario)-[:PARTICIPA_EN]->(p) RETURN DISTINCT m.nombre } AS miembros_conocidos
RETURN c.id AS id, c.nombre AS nombre, c.titular AS titular,
       round(2 * size(domina) + 1.5 * size(miembros_conocidos), 1) AS puntaje,
       domina AS tecnologias, round(nivel, 1) AS nivel_promedio, miembros_conocidos
ORDER BY puntaje DESC, nivel_promedio DESC, nombre
LIMIT $limite
"""

Q_PROYECTOS_RELACIONADOS = """
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
ORDER BY puntaje DESC, proyecto
"""

Q_PARES_PROYECTOS = """
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
LIMIT $limite
"""


def recomendar_contactos(id: str, limite: int = 10) -> list[dict]:
    return leer(Q_RECOMENDAR_CONTACTOS, id=id, limite=int(limite))


def recomendar_empleos(id: str, limite: int = 10) -> list[dict]:
    return leer(Q_RECOMENDAR_EMPLEOS, id=id, limite=int(limite))


def recomendar_candidatos(oferta_id: str, limite: int = 10) -> list[dict]:
    return leer(Q_RECOMENDAR_CANDIDATOS, oferta_id=oferta_id, limite=int(limite))


def recomendar_colaboradores(id: str, limite: int = 10) -> list[dict]:
    return leer(Q_RECOMENDAR_COLABORADORES_USUARIO, id=id, limite=int(limite))


def colaboradores_para_proyecto(proyecto_id: str, limite: int = 10) -> list[dict]:
    return leer(Q_RECOMENDAR_COLABORADORES_PROYECTO, proyecto_id=proyecto_id, limite=int(limite))


def proyectos_relacionados(proyecto_id: str) -> list[dict]:
    return leer(Q_PROYECTOS_RELACIONADOS, proyecto_id=proyecto_id)


def pares_proyectos_relacionados(limite: int = 20) -> list[dict]:
    return leer(Q_PARES_PROYECTOS, limite=int(limite))
