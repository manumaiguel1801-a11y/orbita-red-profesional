// Esquema de Órbita: restricciones de unicidad e índices

CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT usuario_email IF NOT EXISTS FOR (u:Usuario) REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT empresa_id IF NOT EXISTS FOR (e:Empresa) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT empresa_nombre IF NOT EXISTS FOR (e:Empresa) REQUIRE e.nombre IS UNIQUE;
CREATE CONSTRAINT habilidad_nombre IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.nombre IS UNIQUE;
CREATE CONSTRAINT proyecto_id IF NOT EXISTS FOR (p:Proyecto) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT oferta_id IF NOT EXISTS FOR (o:Oferta) REQUIRE o.id IS UNIQUE;

CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre);
CREATE INDEX usuario_ciudad IF NOT EXISTS FOR (u:Usuario) ON (u.ciudad);
CREATE INDEX habilidad_categoria IF NOT EXISTS FOR (h:Habilidad) ON (h.categoria);
CREATE INDEX oferta_activa IF NOT EXISTS FOR (o:Oferta) ON (o.activa);
CREATE INDEX usuario_sesion IF NOT EXISTS FOR (u:Usuario) ON (u.sesion_hash);
