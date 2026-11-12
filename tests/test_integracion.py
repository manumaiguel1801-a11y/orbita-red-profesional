"""Pruebas de integración REALES contra Neo4j AuraDB (lectura y escritura).

Cada prueba crea entidades con prefijo TEST-, verifica el resultado en la base y las elimina.
"""
import pytest
from neo4j.exceptions import ConstraintError

from orbita import analitica as an
from orbita import catalogo as cat
from orbita import datos_demo, esquema, red
from orbita import recomendaciones as rec
from orbita import usuarios as us
from orbita.db import leer


def _u(n, **extra):
    return us.crear_usuario({"nombre": f"TEST-Usuario {n}", "email": f"test-{n}@ejemplo.test",
                             "titular": "Perfil de prueba", "ciudad": "Prueba", "anios_experiencia": 3, **extra}, id=f"TEST-U{n}")


# ------------------------------------------------------------------ Conexión y esquema
def test_conexion_y_restricciones():
    assert leer("RETURN 1 AS x")[0]["x"] == 1
    nombres = {r["name"] for r in esquema.listar_restricciones()}
    assert {"usuario_id", "usuario_email", "empresa_id", "habilidad_nombre", "proyecto_id", "oferta_id"} <= nombres


def test_unicidad_email(limpio):
    _u(1)
    with pytest.raises(ConstraintError):
        us.crear_usuario({"nombre": "TEST-Otro", "email": "TEST-1@ejemplo.test".lower()}, id="TEST-U99")


# ------------------------------------------------------------------ A1-A4 CRUD usuarios
def test_crud_usuario(limpio):
    u = _u(1, telefono="123", nivel_educativo="Maestría")
    assert u["id"] == "TEST-U1" and u["fecha_registro"]
    assert any(x["id"] == "TEST-U1" for x in us.listar_usuarios("TEST-Usuario"))
    p = us.obtener_usuario("TEST-U1")
    assert p["usuario"]["email"] == "test-1@ejemplo.test" and p["usuario"]["nivel_educativo"] == "Maestría"
    us.actualizar_usuario("TEST-U1", {"titular": "Titular editado", "anios_experiencia": "7"})
    p = us.obtener_usuario("TEST-U1")["usuario"]
    assert p["titular"] == "Titular editado" and p["anios_experiencia"] == 7 and p["actualizado"]
    us.asignar_habilidad("TEST-U1", "TEST-Hab", 4)
    assert us.eliminar_usuario("TEST-U1") == 1          # tenía 1 relación
    assert us.obtener_usuario("TEST-U1") is None
    assert us.eliminar_usuario("TEST-U1") is None        # ya no existe


def test_crear_usuario_valida_obligatorios(limpio):
    with pytest.raises(ValueError):
        us.crear_usuario({"nombre": "TEST-Sin correo"})


# ------------------------------------------------------------------ A5 Conexiones
def test_conexiones(limpio):
    _u(1); _u(2)
    assert us.conectar("TEST-U1", "TEST-U2")["destino"] == "TEST-Usuario 2"
    assert us.conectar("TEST-U2", "TEST-U1") is None     # simétrica: no se duplica
    assert red.estan_conectados("TEST-U2", "TEST-U1")
    with pytest.raises(ValueError):
        us.conectar("TEST-U1", "TEST-U1")
    assert us.desconectar("TEST-U2", "TEST-U1") == 1
    assert not red.estan_conectados("TEST-U1", "TEST-U2")


# ------------------------------------------------------------------ A6-A8 Vínculos
def test_vinculos_habilidad_empresa_proyecto(limpio):
    _u(1)
    cat.crear_empresa({"nombre": "TEST-Empresa", "sector": "Pruebas"}, id="TEST-E1")
    cat.crear_proyecto({"nombre": "TEST-Proyecto", "estado": "En curso"}, ["TEST-Hab"], id="TEST-P1")
    us.asignar_habilidad("TEST-U1", "TEST-Hab", 2)
    us.asignar_habilidad("TEST-U1", "TEST-Hab", 5)       # actualiza nivel, no duplica
    us.vincular_empresa("TEST-U1", "TEST-E1", "Probador", 2020, True)
    us.vincular_proyecto("TEST-U1", "TEST-P1", "Líder")
    p = us.obtener_usuario("TEST-U1")
    assert p["habilidades"] == [{"habilidad": "TEST-Hab", "categoria": "General", "nivel": 5}]
    assert p["empresas"][0]["cargo"] == "Probador" and p["empresas"][0]["actual"] is True
    assert p["proyectos"][0]["rol"] == "Líder"
    assert us.quitar_habilidad("TEST-U1", "TEST-Hab") == 1
    assert us.desvincular_empresa("TEST-U1", "TEST-E1") == 1
    assert us.desvincular_proyecto("TEST-U1", "TEST-P1") == 1
    p = us.obtener_usuario("TEST-U1")
    assert not p["habilidades"] and not p["empresas"] and not p["proyectos"]


# ------------------------------------------------------------------ A9-A12 Empresas, ofertas, requisitos, postulación
def test_empresas_ofertas_requisitos_postulacion(limpio):
    _u(1)
    cat.crear_empresa({"nombre": "TEST-Empresa"}, id="TEST-E1")
    assert cat.actualizar_empresa("TEST-E1", {"ciudad": "Ciudad Test"})["ciudad"] == "Ciudad Test"
    r = cat.crear_oferta("TEST-E1", {"titulo": "TEST-Oferta", "modalidad": "Remoto"},
                         [{"habilidad": "TEST-HabA", "nivel_minimo": 3, "obligatoria": True},
                          {"habilidad": "TEST-HabB", "nivel_minimo": 2, "obligatoria": False}], id="TEST-O1")
    assert r == {"id": "TEST-O1", "empresa": "TEST-Empresa", "habilidades": 2}
    assert leer("MATCH (:Empresa {id:'TEST-E1'})-[:PUBLICA]->(o:Oferta {id:'TEST-O1'}) RETURN count(o) AS c")[0]["c"] == 1
    cat.agregar_requisito("TEST-O1", "TEST-HabC", 4, True)
    assert cat.quitar_requisito("TEST-O1", "TEST-HabB") == 1
    o = next(x for x in cat.listar_ofertas(False, "TEST-E1"))
    assert {x["habilidad"] for x in o["requisitos"]} == {"TEST-HabA", "TEST-HabC"}
    # postulación (idempotente)
    p = us.postular("TEST-U1", "TEST-O1")
    assert p["estado"] == "Enviada"
    us.postular("TEST-U1", "TEST-O1")
    assert len(cat.postulantes("TEST-O1")) == 1
    us.cambiar_estado_postulacion("TEST-U1", "TEST-O1", "Entrevista")
    assert cat.postulantes("TEST-O1")[0]["estado"] == "Entrevista"
    assert us.retirar_postulacion("TEST-U1", "TEST-O1") == 1
    # oferta cerrada => no admite postulaciones
    cat.actualizar_oferta("TEST-O1", {"activa": False})
    assert us.postular("TEST-U1", "TEST-O1") is None
    # eliminar empresa elimina en cascada sus ofertas
    assert cat.eliminar_empresa("TEST-E1") == 1
    assert not leer("MATCH (o:Oferta {id:'TEST-O1'}) RETURN o")


def test_crud_habilidad_y_proyecto(limpio):
    cat.crear_habilidad("TEST-Hab", "Pruebas")
    assert cat.actualizar_habilidad("TEST-Hab", "TEST-Hab2", "Otra")["categoria"] == "Otra"
    assert cat.eliminar_habilidad("TEST-Hab2") == 0
    cat.crear_proyecto({"nombre": "TEST-Proyecto"}, ["TEST-T1"], id="TEST-P1")
    cat.agregar_tecnologia("TEST-P1", "TEST-T2")
    assert cat.quitar_tecnologia("TEST-P1", "TEST-T1") == 1
    assert cat.actualizar_proyecto("TEST-P1", {"estado": "Finalizado"})["estado"] == "Finalizado"
    assert next(p for p in cat.listar_proyectos() if p["id"] == "TEST-P1")["tecnologias"] == ["TEST-T2"]
    assert cat.eliminar_proyecto("TEST-P1") == 1


# ------------------------------------------------------------------ Escenario de red aislado y determinista
@pytest.fixture()
def mini_red(limpio):
    """
    U1 —— U2 —— U3 ——(TRABAJA_EN actual)—> E1 —PUBLICA→ O1 —REQUIERE→ HabA(ob,3), HabB(ob,3), HabC(des,2)
     \\____ U4 ___/
    U1: HabA(4), HabB(2), HabX(3)     U2: HabA(3), HabX(3)     U4: HabX(1)
    """
    for i in range(1, 5):
        _u(i)
    for a, b in [(1, 2), (2, 3), (1, 4), (4, 2)]:
        us.conectar(f"TEST-U{a}", f"TEST-U{b}")
    cat.crear_empresa({"nombre": "TEST-Empresa"}, id="TEST-E1")
    us.vincular_empresa("TEST-U3", "TEST-E1", "Reclutadora", 2020, True)
    cat.crear_oferta("TEST-E1", {"titulo": "TEST-Oferta"},
                     [{"habilidad": "TEST-HabA", "nivel_minimo": 3, "obligatoria": True},
                      {"habilidad": "TEST-HabB", "nivel_minimo": 3, "obligatoria": True},
                      {"habilidad": "TEST-HabC", "nivel_minimo": 2, "obligatoria": False}], id="TEST-O1")
    for u, h, n in [(1, "A", 4), (1, "B", 2), (1, "X", 3), (2, "A", 3), (2, "X", 3), (4, "X", 1)]:
        us.asignar_habilidad(f"TEST-U{u}", f"TEST-Hab{h}", n)
    cat.crear_proyecto({"nombre": "TEST-P1"}, ["TEST-HabA", "TEST-HabX"], id="TEST-P1")
    cat.crear_proyecto({"nombre": "TEST-P2"}, ["TEST-HabA"], id="TEST-P2")
    us.vincular_proyecto("TEST-U1", "TEST-P1")
    us.vincular_proyecto("TEST-U2", "TEST-P2")
    yield


def test_contactos_en_comun(mini_red):
    comunes = red.contactos_en_comun("TEST-U1", "TEST-U3")
    assert [c["id"] for c in comunes] == ["TEST-U2"]
    assert {c["id"] for c in red.contactos_en_comun("TEST-U1", "TEST-U2")} == {"TEST-U4"}


def test_ruta_mas_corta_usuario_empresa_y_oferta(mini_red):
    r = red.ruta_mas_corta("Usuario", "TEST-U1", "Empresa", "TEST-E1", ["CONECTA_CON", "TRABAJA_EN"])
    assert r[0]["saltos"] == 3
    assert [n["id"] for n in r[0]["nodos"]] == ["TEST-U1", "TEST-U2", "TEST-U3", "TEST-E1"]
    assert r[0]["relaciones"] == ["CONECTA_CON", "CONECTA_CON", "TRABAJA_EN"]
    r = red.ruta_mas_corta("Usuario", "TEST-U4", "Oferta", "TEST-O1", ["CONECTA_CON", "TRABAJA_EN", "PUBLICA"])
    assert r[0]["saltos"] == 4 and r[0]["nodos"][-1]["etiqueta"] == "Oferta"
    # por habilidades, el camino es más corto: U1 -TIENE_HABILIDAD-> HabA <-REQUIERE- O1
    r = red.ruta_mas_corta("Usuario", "TEST-U1", "Oferta", "TEST-O1", ["TIENE_HABILIDAD", "REQUIERE"])
    assert r[0]["saltos"] == 2
    todas = red.ruta_mas_corta("Usuario", "TEST-U1", "Usuario", "TEST-U3", ["CONECTA_CON"], todas=True)
    assert len(todas) == 1 and todas[0]["saltos"] == 2
    assert red.grado_separacion("TEST-U4", "TEST-U3")["grado"] == 2


def test_usuarios_similares_jaccard(mini_red):
    sim = {s["id"]: s for s in red.usuarios_similares("TEST-U1", 50)}
    # U1={A,B,X}, U2={A,X} => 2/3 ; U4={X} => 1/3
    assert sim["TEST-U2"]["jaccard"] == pytest.approx(0.667, abs=1e-3)
    assert sim["TEST-U4"]["jaccard"] == pytest.approx(0.333, abs=1e-3)


def test_recomendar_contactos(mini_red):
    r = {x["id"]: x for x in rec.recomendar_contactos("TEST-U1", 50)}
    # U3: 1 contacto en común (U2), sin habilidades compartidas => 3 puntos
    assert r["TEST-U3"]["puntaje"] == 3 and r["TEST-U3"]["comunes"] == ["TEST-Usuario 2"]
    assert "TEST-U2" not in r            # ya conectados


def test_recomendar_candidatos_formula(mini_red):
    c = {x["id"]: x for x in rec.recomendar_candidatos("TEST-O1", 100)}
    # U1: HabA 4>=3 -> 2 ; HabB 2<3 -> 1 ; HabC no -> 0  => cobertura 3/5 = 0.6
    #     red: contactos directos en E1 = 0 ; 2.º grado (U3 vía U2) = 1 => red = 0.5/3
    #     puntaje = 100·(0.7·0.6 + 0.3·0.1667) = 47.0
    assert c["TEST-U1"]["cobertura_pct"] == 60.0
    assert c["TEST-U1"]["contactos_2do_grado"] == 1
    assert c["TEST-U1"]["puntaje"] == 47.0
    # U2: HabA -> 2 => cobertura 0.4 ; contacto directo U3 en E1 => red 1/3 => 100·(0.28+0.1) = 38.0
    assert c["TEST-U2"]["puntaje"] == 38.0 and c["TEST-U2"]["contactos_en_empresa"] == ["TEST-Usuario 3"]
    assert "TEST-U3" not in c            # ya trabaja en la empresa
    assert "TEST-U4" not in c            # cobertura 0


def test_recomendar_empleos(mini_red):
    e = {x["oferta_id"]: x for x in rec.recomendar_empleos("TEST-U1", 100)}
    assert e["TEST-O1"]["puntaje"] == 47.0 and e["TEST-O1"]["faltan"] == ["TEST-HabC"]
    us.postular("TEST-U1", "TEST-O1")
    assert "TEST-O1" not in {x["oferta_id"] for x in rec.recomendar_empleos("TEST-U1", 100)}


def test_colaboradores_y_proyectos_relacionados(mini_red):
    col = {x["id"]: x for x in rec.recomendar_colaboradores("TEST-U1", 100)}
    # Tecnologías de P1 = {HabA, HabX}; U2 tiene ambas y está conectado; 1 contacto común (U4) => 2·2 + 3 + 1 = 8
    assert col["TEST-U2"]["puntaje"] == 8
    rel = {x["id"]: x for x in rec.proyectos_relacionados("TEST-P1")}
    # comparten HabA (2) + pares de miembros conectados U1↔U2 (1) => 3
    assert rel["TEST-P2"]["tecnologias_compartidas"] == ["TEST-HabA"]
    assert rel["TEST-P2"]["puntaje"] == 3
    para_p2 = {x["id"]: x for x in rec.colaboradores_para_proyecto("TEST-P2", 100)}
    assert para_p2["TEST-U1"]["miembros_conocidos"] == ["TEST-Usuario 2"]


# ------------------------------------------------------------------ Analítica sobre los datos de demostración
def test_habilidades_mas_demandadas():
    dem = an.habilidades_demandadas(5)
    assert dem and dem[0]["ofertas"] >= dem[-1]["ofertas"]
    manual = leer("MATCH (o:Oferta)-[:REQUIERE]->(h:Habilidad {nombre: $h}) WHERE o.activa RETURN count(o) AS c", h=dem[0]["habilidad"])
    assert manual[0]["c"] == dem[0]["ofertas"]


def test_usuarios_influyentes():
    inf = an.usuarios_influyentes(5)
    assert len(inf) == 5 and inf[0]["indice_influencia"] == 100.0
    assert all(0 <= x["pagerank"] <= 1 for x in inf)


def test_pagerank_suma_uno():
    pr = an.pagerank(an.grafo_conexiones())
    assert sum(pr.values()) == pytest.approx(1.0, abs=1e-6)


def test_comunidades():
    louvain = an.comunidades("louvain")
    comp = an.comunidades("componentes")
    assert len({f["comunidad"] for f in louvain}) >= len({f["comunidad"] for f in comp})
    assert an.modularidad(louvain) > 0.3
    assert an.comunidades("louvain") == louvain       # reproducible (semilla fija)


def test_carga_demo_idempotente():
    datos_demo.cargar()
    antes = (esquema.conteo_nodos(), esquema.conteo_relaciones())
    datos_demo.cargar()
    assert (esquema.conteo_nodos(), esquema.conteo_relaciones()) == antes


def test_borrado_requiere_confirmacion():
    with pytest.raises(PermissionError):
        esquema.borrar_todo("si")
    assert esquema.total_nodos() > 0


# ------------------------------------------------------------------ Perfil público y empresas creadas por usuarios
def test_perfil_publico_muestra_lo_que_comparten(mini_red):
    p = us.perfil_publico("TEST-U1", "TEST-U3")          # no conectados; U2 es contacto común
    assert p["conectados"] is False and p["grado"] == 2
    assert p["contactos_en_comun"] == ["TEST-Usuario 2"]
    assert p["email"] is None and p["telefono"] is None   # privacidad: sin datos de contacto
    q = us.perfil_publico("TEST-U1", "TEST-U2")          # conectados
    assert q["conectados"] is True and q["email"] == "test-2@ejemplo.test"
    compartidas = {h["habilidad"]: h["compartida"] for h in q["habilidades"]}
    assert compartidas == {"TEST-HabA": True, "TEST-HabX": True}
    us.enviar_invitacion("TEST-U1", "TEST-U3")
    assert us.perfil_publico("TEST-U1", "TEST-U3")["invitacion_enviada"] is True
    assert us.perfil_publico("TEST-U3", "TEST-U1")["invitacion_recibida"] is True
    assert us.perfil_publico("TEST-U1", "TEST-NOEXISTE") is None


def test_registrar_empresa_sin_duplicados(limpio):
    e = cat.registrar_empresa({"nombre": "TEST-Mi  Empresa", "sector": "Pruebas", "ciudad": "Cali"})
    assert e["ya_existia"] is False and e["nombre"] == "TEST-Mi Empresa"
    otra = cat.registrar_empresa({"nombre": "  test-mi empresa "})
    assert otra["ya_existia"] is True and otra["id"] == e["id"]
    with pytest.raises(ValueError):
        cat.registrar_empresa({"nombre": "A"})
