"""Sistema de diseño de Órbita: tokens, íconos SVG de línea, CSS global con animaciones y componentes HTML.

Identidad: tema oscuro, violeta eléctrico (#8B5CF6) como primario y lima (#A3E635) como acento.
Sin emojis: toda la iconografía es SVG de trazo (estilo Lucide) o Material Symbols nativos de Streamlit.
"""
from __future__ import annotations

import hashlib
import html as _html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

VIOLETA, VIOLETA_2, LIMA, CIAN, ROSA, NARANJA = "#8B5CF6", "#A78BFA", "#A3E635", "#22D3EE", "#F472B6", "#FB923C"
FONDO, SUPERFICIE, BORDE, TEXTO, MUTED = "#09090B", "#111114", "#26262B", "#FAFAFA", "#A1A1AA"
AVATAR_COLORES = ["#8B5CF6", "#6366F1", "#22D3EE", "#A3E635", "#F472B6", "#FB923C", "#2DD4BF", "#C084FC", "#38BDF8", "#FACC15"]
ROL_ESTILO = {"admin": ("Administrador", "#E9D5FF", "rgba(168,85,247,.22)"),
              "reclutador": ("Reclutador", "#A5F3FC", "rgba(34,211,238,.16)"),
              "profesional": ("Profesional", "#D9F99D", "rgba(163,230,53,.14)")}
TONOS = {"violeta": ("#C4B5FD", "rgba(139,92,246,.16)"), "lima": ("#D9F99D", "rgba(163,230,53,.13)"),
         "cian": ("#A5F3FC", "rgba(34,211,238,.13)"), "rosa": ("#FBCFE8", "rgba(244,114,182,.14)"),
         "naranja": ("#FED7AA", "rgba(251,146,60,.14)"), "gris": ("#D4D4D8", "rgba(161,161,170,.12)")}

# ---------------------------------------------------------------- Íconos (trazos SVG, viewBox 24)
_P = {
    "inicio": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/>',
    "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/>',
    "usuarios": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8"/><path d="M18 14.3c2 .7 3.5 2.6 3.5 5.7"/>',
    "conexion": '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8 7.5 10.8 16M16 7.5 13.2 16M8.5 6h7"/>',
    "maletin": '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M3 12.5h18"/>',
    "empresa": '<rect x="4" y="3" width="11" height="18" rx="1.5"/><path d="M15 9h4a1 1 0 0 1 1 1v11H15"/><path d="M8 7h3M8 11h3M8 15h3"/>',
    "habilidad": '<path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z"/>',
    "proyecto": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "enviar": '<path d="M21 3 10 14"/><path d="M21 3 14.5 21l-4-7-7-4z"/>',
    "campana": '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2.2 2.2 0 0 0 4 0"/>',
    "red": '<circle cx="12" cy="12" r="2.5"/><circle cx="4.5" cy="5" r="2"/><circle cx="19.5" cy="5" r="2"/><circle cx="4.5" cy="19" r="2"/><circle cx="19.5" cy="19" r="2"/><path d="M6 6.5 10.2 10.3M18 6.5l-4.2 3.8M6 17.5l4.2-3.8M18 17.5l-4.2-3.8"/>',
    "grafica": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "chispa": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
    "brujula": '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
    "ajustes": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3 14.4H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 9.6 4V3.9a2 2 0 1 1 4 0V4a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7h.1a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-.8.4z"/>',
    "objetivo": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "lista": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h4"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
    "ojo": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "trofeo": '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 21h7M10 17h4"/>',
    "cerrar": '<path d="M6 6l12 12M18 6 6 18"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "escudo": '<path d="M12 3 4.5 6v6c0 4.5 3.2 7.8 7.5 9 4.3-1.2 7.5-4.5 7.5-9V6z"/>',
    "bloqueo": '<circle cx="12" cy="12" r="9"/><path d="M5.7 5.7l12.6 12.6"/>',
    "bandeja": '<path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M5.5 5h13L21 13v6H3v-6z"/>',
    "buscar": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>',
    "brote": '<path d="M12 21v-9"/><path d="M12 12c0-4 3-7 8-7 0 5-3 7-8 7z"/><path d="M12 14c0-3-2.5-5.5-7-5.5 0 4 2.5 5.5 7 5.5z"/>',
    "enlace": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "candado": '<rect x="4.5" y="10.5" width="15" height="10.5" rx="2.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    "matraz": '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/><path d="M7 15h10"/>',
    "papelera": '<path d="M4 7h16M10 11v6M14 11v6M5.5 7l1 13h11l1-13M9 7V4h6v3"/>',
    "alerta": '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17.5v.01"/>',
    "tendencia": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "salir": '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l5-5-5-5M15 12H3"/>',
    "ubicacion": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "correo": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6 8.5 7 8.5-7"/>',
    "birrete": '<path d="M2 9 12 4l10 5-10 5z"/><path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5"/>',
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendario": '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "mas": '<path d="M12 5v14M5 12h14"/>',
    "orbita": '<circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-25 12 12)"/>',
    "codigo": '<path d="m8 7-5 5 5 5M16 7l5 5-5 5"/>',
    "ruta": '<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/><path d="M8.5 19H16a3.5 3.5 0 0 0 0-7H8a3.5 3.5 0 0 1 0-7h7.5"/>',
}


def icono(nombre: str, tam: int = 18, color: str = "currentColor", grosor: float = 1.8) -> str:
    return (f'<svg class="ox-ic" width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_P.get(nombre, _P["chispa"])}</svg>')


# ---------------------------------------------------------------- Plotly: plantilla oscura de la marca
pio.templates["orbita"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#D4D4D8", size=12),
    colorway=[VIOLETA, LIMA, CIAN, ROSA, NARANJA, "#818CF8", "#2DD4BF", "#FACC15"],
    xaxis=dict(gridcolor="#1F1F24", zerolinecolor="#26262B", linecolor="#26262B"),
    yaxis=dict(gridcolor="#1F1F24", zerolinecolor="#26262B", linecolor="#26262B"),
    legend=dict(bgcolor="rgba(0,0,0,0)"), hoverlabel=dict(bgcolor="#18181B", bordercolor=VIOLETA, font_color="#FAFAFA"),
    colorscale=dict(sequential=[[0, "#2E1065"], [0.5, VIOLETA], [1, LIMA]],
                    sequentialminus=[[0, "#2E1065"], [0.5, VIOLETA], [1, LIMA]]),
    coloraxis=dict(colorscale=[[0, "#2E1065"], [0.5, VIOLETA], [1, LIMA]])))
pio.templates.default = "plotly_dark+orbita"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--v:#8B5CF6;--v2:#A78BFA;--v3:#6D28D9;--l:#A3E635;--c:#22D3EE;--bg:#09090B;--sf:#111114;--sf2:#18181B;--brd:#26262B;
      --tx:#FAFAFA;--tx2:#D4D4D8;--mut:#A1A1AA;--ok:#A3E635;--bad:#F87171;--r:18px;}
html,body,[class*="css"],.stApp,button,input,textarea,select{font-family:'Inter',system-ui,'Segoe UI',sans-serif!important;}
h1,h2,h3,.ox-display{font-family:'Space Grotesk','Inter',sans-serif!important;letter-spacing:-.02em;}
.stApp{background:radial-gradient(900px 500px at 100% -10%,rgba(139,92,246,.13),transparent 60%),
                  radial-gradient(700px 400px at -10% 110%,rgba(163,230,53,.05),transparent 60%),var(--bg);}
.block-container{padding-top:1.5rem;padding-bottom:3rem;max-width:1280px;}
footer,#MainMenu{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stDecoration"]{background:linear-gradient(90deg,var(--v),var(--c),var(--l));height:2px;}
::selection{background:rgba(139,92,246,.45);}
[data-testid="stElementContainer"]:has(iframe[height="0"]){display:none;}

/* ---------------- Animaciones ---------------- */
@keyframes ox-subir{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes ox-aparecer{from{opacity:0}to{opacity:1}}
@keyframes ox-crecer{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes ox-girar{to{transform:rotate(360deg)}}
@keyframes ox-girar-inv{to{transform:rotate(-360deg)}}
@keyframes ox-flotar{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes ox-pulso{0%{box-shadow:0 0 0 0 rgba(163,230,53,.55)}70%{box-shadow:0 0 0 10px rgba(163,230,53,0)}100%{box-shadow:0 0 0 0 rgba(163,230,53,0)}}
@keyframes ox-degradado{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes ox-brillo{from{transform:translateX(-120%) skewX(-20deg)}to{transform:translateX(220%) skewX(-20deg)}}
@keyframes ox-trazo{from{stroke-dashoffset:100}}
.block-container > div > div > div > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0){animation:ox-subir .5s cubic-bezier(.2,.7,.2,1) both;}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) > div{animation-delay:.06s;}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) > div{animation-delay:.12s;}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;}}

/* ---------------- Barra lateral ---------------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0C0C10 0%,#0A0A0D 100%);border-right:1px solid #1C1C21;}
[data-testid="stSidebar"] *{color:#A1A1AA;}
[data-testid="stSidebarNav"] a{border-radius:11px;margin:2px 8px;padding:.42rem .75rem;position:relative;transition:background .2s,color .2s;}
[data-testid="stSidebarNav"] a:hover{background:#17171C;}
[data-testid="stSidebarNav"] a:hover span{color:#F4F4F5!important;}
[data-testid="stSidebarNav"] a[aria-current="page"]{background:linear-gradient(90deg,rgba(139,92,246,.24),rgba(139,92,246,.04));}
[data-testid="stSidebarNav"] a[aria-current="page"]::before{content:"";position:absolute;left:-8px;top:22%;bottom:22%;width:3px;border-radius:3px;
   background:linear-gradient(var(--v),var(--l));animation:ox-aparecer .3s both;}
[data-testid="stSidebarNav"] a[aria-current="page"] span{color:#fff!important;font-weight:600;}
[data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"]{color:var(--v2)!important;}
[data-testid="stNavSectionHeader"]{color:#52525B!important;font-size:.66rem!important;letter-spacing:.12em;text-transform:uppercase;font-weight:700;margin-top:.7rem;}
[data-testid="stSidebar"] .stButton button{background:#141418;border:1px solid #26262B;color:#D4D4D8;}
[data-testid="stSidebar"] .stButton button:hover{border-color:var(--v);color:#fff;background:#18181F;}

/* ---------------- Controles ---------------- */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:12px;font-weight:600;padding:.48rem 1.05rem;
   border:1px solid var(--brd);background:var(--sf2);color:var(--tx2);transition:all .2s ease;position:relative;overflow:hidden;}
.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:var(--v);color:#fff;transform:translateY(-1px);}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#7C3AED,#8B5CF6 45%,#A78BFA);
   border:0;color:#fff;box-shadow:0 8px 24px -10px rgba(139,92,246,.9),inset 0 1px 0 rgba(255,255,255,.18);}
.stButton>button[kind="primary"]::after,.stFormSubmitButton>button[kind="primaryFormSubmit"]::after{content:"";position:absolute;top:0;left:0;width:40%;height:100%;
   background:linear-gradient(90deg,transparent,rgba(255,255,255,.28),transparent);transform:translateX(-120%) skewX(-20deg);}
.stButton>button[kind="primary"]:hover::after,.stFormSubmitButton>button[kind="primaryFormSubmit"]:hover::after{animation:ox-brillo .7s ease;}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primaryFormSubmit"]:hover{box-shadow:0 12px 30px -10px rgba(139,92,246,1);}
.stButton>button:disabled{opacity:.55;transform:none;}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{border-radius:12px!important;background:#121216!important;border:1px solid #2E2E35!important;transition:border-color .2s,box-shadow .2s;}
[data-baseweb="input"]:hover,[data-baseweb="textarea"]:hover,[data-baseweb="select"]>div:hover{border-color:#3F3F46!important;}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--v)!important;box-shadow:0 0 0 3px rgba(139,92,246,.25)!important;}
[data-baseweb="input"] input,[data-baseweb="input"] > div{background:transparent!important;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0){background:linear-gradient(180deg,#131317,#101013);
   border-radius:var(--r)!important;border-color:var(--brd)!important;transition:border-color .25s,box-shadow .25s,transform .25s;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0):hover{border-color:rgba(139,92,246,.45)!important;
   box-shadow:0 0 0 1px rgba(139,92,246,.12),0 18px 40px -22px rgba(139,92,246,.6);}
[data-testid="stExpander"] details{border-radius:14px;border-color:var(--brd);background:#101013;}
[data-testid="stExpander"] summary:hover{color:var(--v2);}
div[data-testid="stMetric"]{background:#111114;border:1px solid var(--brd);border-radius:16px;padding:.8rem 1rem;}
div[data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif;font-weight:700;}
[data-testid="stDataFrame"]{border-radius:14px;overflow:hidden;border:1px solid var(--brd);}
[data-testid="stAlert"]{border-radius:14px;}
.stCheckbox [data-baseweb="checkbox"] span:first-child{border-radius:6px;}

/* ---------------- Pestañas tipo píldora ---------------- */
.stTabs [data-baseweb="tab-list"]{gap:.3rem;background:#111114;border:1px solid var(--brd);padding:.3rem;border-radius:14px;width:fit-content;max-width:100%;overflow-x:auto;}
.stTabs [data-baseweb="tab"]{height:2.25rem;border-radius:10px;padding:0 1rem;background:transparent;font-weight:500;color:var(--mut);white-space:nowrap;transition:color .2s,background .2s;}
.stTabs [data-baseweb="tab"]:hover{color:var(--tx);}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(139,92,246,.95),rgba(124,58,237,.95))!important;color:#fff!important;
   box-shadow:0 6px 18px -8px rgba(139,92,246,.9);font-weight:600;}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-baseweb="tab-panel"]{animation:ox-aparecer .35s ease both;padding-top:1rem;}

/* ---------------- Componentes Órbita ---------------- */
.ox-ic{display:inline-block;vertical-align:-.18em;flex:0 0 auto;}
.ox-head{display:flex;align-items:center;gap:1rem;margin:.2rem 0 1.3rem;animation:ox-subir .45s ease both;}
.ox-head .ic{width:50px;height:50px;border-radius:15px;display:flex;align-items:center;justify-content:center;color:#E9D5FF;
   background:linear-gradient(135deg,rgba(139,92,246,.35),rgba(139,92,246,.08));border:1px solid rgba(139,92,246,.4);
   box-shadow:0 10px 30px -12px rgba(139,92,246,.8);}
.ox-head h1{font-size:1.7rem;margin:0;padding:0;font-weight:700;color:var(--tx);}
.ox-head p{margin:.15rem 0 0;color:var(--mut);font-size:.93rem;}
.ox-hero{border-radius:24px;padding:1.7rem 1.9rem;color:#fff;margin-bottom:1.2rem;position:relative;overflow:hidden;
   background:linear-gradient(120deg,#2E1065,#5B21B6 40%,#7C3AED 70%,#4C1D95);background-size:220% 220%;
   animation:ox-degradado 14s ease infinite,ox-subir .5s ease both;border:1px solid rgba(167,139,250,.35);
   box-shadow:0 25px 60px -28px rgba(139,92,246,.9);}
.ox-hero::after{content:"";position:absolute;right:-60px;top:-80px;width:320px;height:320px;border-radius:50%;
   border:1px dashed rgba(255,255,255,.18);animation:ox-girar 40s linear infinite;}
.ox-hero::before{content:"";position:absolute;right:40px;top:-30px;width:180px;height:180px;border-radius:50%;
   border:1px solid rgba(163,230,53,.25);animation:ox-girar-inv 26s linear infinite;}
.ox-hero h2{color:#fff;margin:0;font-size:1.75rem;font-weight:700;}
.ox-hero p{color:#E9D5FF;margin:.3rem 0 0;}
.ox-card{background:linear-gradient(180deg,#131317,#101013);border:1px solid var(--brd);border-radius:var(--r);padding:1rem 1.15rem;margin-bottom:.8rem;
   transition:border-color .25s,transform .25s,box-shadow .25s;animation:ox-subir .45s ease both;}
.ox-card:hover{border-color:rgba(139,92,246,.45);transform:translateY(-2px);box-shadow:0 18px 40px -22px rgba(139,92,246,.6);}
.ox-row{display:flex;gap:.9rem;align-items:flex-start;}
.ox-av{flex:0 0 auto;border-radius:50%;color:#0B0B0F;display:flex;align-items:center;justify-content:center;font-weight:800;letter-spacing:.02em;
   box-shadow:0 0 0 2px #0B0B0F,0 0 0 3.5px rgba(139,92,246,.55);}
.ox-logo-emp{flex:0 0 auto;width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-weight:800;
   font-family:'Space Grotesk',sans-serif;border:1px solid rgba(255,255,255,.08);}
.ox-t{font-weight:700;color:var(--tx);font-size:1rem;line-height:1.25;}
.ox-s{color:var(--mut);font-size:.86rem;margin-top:.12rem;}
.ox-meta{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.5rem;}
.ox-pill{display:inline-flex;align-items:center;gap:.3rem;font-size:.76rem;padding:.18rem .6rem;border-radius:999px;background:#18181D;color:#D4D4D8;
   border:1px solid #2A2A30;transition:border-color .2s;}
.ox-pill:hover{border-color:#3F3F46;}
.ox-pill.ok{background:rgba(163,230,53,.1);color:#D9F99D;border-color:rgba(163,230,53,.35);}
.ox-pill.no{background:rgba(248,113,113,.08);color:#FCA5A5;border-color:rgba(248,113,113,.3);}
.ox-pill.ind{background:rgba(139,92,246,.14);color:#DDD6FE;border-color:rgba(139,92,246,.4);}
.ox-pill.warn{background:rgba(251,191,36,.1);color:#FDE68A;border-color:rgba(251,191,36,.3);}
.ox-badge{display:inline-flex;align-items:center;font-size:.68rem;font-weight:700;padding:.14rem .55rem;border-radius:7px;letter-spacing:.04em;text-transform:uppercase;}
.ox-ring{flex:0 0 auto;width:64px;height:64px;position:relative;display:flex;align-items:center;justify-content:center;}
.ox-ring svg{position:absolute;inset:0;width:100%;height:100%;}
.ox-ring .arco{animation:ox-trazo 1.3s cubic-bezier(.2,.7,.2,1) both;filter:drop-shadow(0 0 3px currentColor);}
.ox-ring span{position:relative;font-weight:700;font-size:.84rem;color:var(--tx);font-family:'Space Grotesk',sans-serif;}
.ox-stat{background:linear-gradient(180deg,#131317,#0F0F12);border:1px solid var(--brd);border-radius:var(--r);padding:1rem 1.1rem;display:flex;gap:.85rem;
   align-items:center;animation:ox-subir .5s ease both;transition:border-color .25s,transform .25s;position:relative;overflow:hidden;}
.ox-stat:hover{border-color:rgba(139,92,246,.5);transform:translateY(-2px);}
.ox-stat .ico{width:44px;height:44px;border-radius:13px;display:flex;align-items:center;justify-content:center;}
.ox-stat .v{font-size:1.6rem;font-weight:700;color:var(--tx);line-height:1.05;font-family:'Space Grotesk',sans-serif;}
.ox-stat .l{font-size:.78rem;color:var(--mut);font-weight:500;}
.ox-bar{height:7px;border-radius:99px;background:#1F1F25;overflow:hidden;margin-top:.4rem;}
.ox-bar>i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--v),var(--c),var(--l));transform-origin:left;
   animation:ox-crecer 1s cubic-bezier(.2,.7,.2,1) both;}
.ox-empty{text-align:center;padding:2.4rem 1rem;border:1px dashed #33333A;border-radius:var(--r);background:#0F0F12;color:var(--mut);animation:ox-subir .45s ease both;}
.ox-empty .e{display:inline-flex;width:56px;height:56px;border-radius:50%;align-items:center;justify-content:center;color:var(--v2);
   background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.35);animation:ox-flotar 4s ease-in-out infinite;}
.ox-empty b{display:block;color:var(--tx);margin:.6rem 0 .2rem;font-size:1.02rem;}
.ox-sec{display:flex;align-items:center;gap:.5rem;font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#71717A;margin:1.2rem 0 .65rem;}
.ox-sec::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,#26262B,transparent);}
.ox-ruta{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;padding:.6rem 0;}
.ox-paso{padding:.34rem .75rem;border-radius:10px;color:#0B0B0F;font-size:.84rem;font-weight:700;animation:ox-subir .4s ease both;}
.ox-flecha{color:#71717A;font-size:.7rem;font-family:ui-monospace,monospace;}
.ox-leyenda span{display:inline-flex;align-items:center;margin-right:1.1rem;font-size:.8rem;color:var(--tx2);}
.ox-leyenda i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:.4rem;box-shadow:0 0 10px currentColor;}
.ox-check{display:flex;gap:.55rem;align-items:center;font-size:.88rem;padding:.25rem 0;color:var(--tx2);}
.ox-check .d{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#0B0B0F;}
.ox-me{display:flex;gap:.65rem;align-items:center;background:#111116;border:1px solid #232329;border-radius:14px;padding:.65rem .75rem;margin:.4rem 0 .55rem;}
.ox-me .n{color:#FAFAFA!important;font-weight:600;font-size:.9rem;line-height:1.15;}
.ox-vivo{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--l);margin-right:.45rem;animation:ox-pulso 2s infinite;}
.ox-err{color:#FCA5A5;font-size:.8rem;margin:-.55rem 0 .55rem .1rem;display:flex;gap:.35rem;align-items:center;}
.ox-fuerza{display:flex;gap:4px;margin:-.35rem 0 .25rem;}
.ox-fuerza i{flex:1;height:5px;border-radius:9px;background:#27272A;transition:background .3s;}
</style>
"""

CSS_AUTH = """
<style>
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],header[data-testid="stHeader"]{display:none!important;}
.block-container{max-width:1200px;padding-top:2.4rem;}
.ox-auth{min-height:640px;border-radius:28px;padding:2.5rem 2.4rem;color:#fff;position:relative;overflow:hidden;animation:ox-subir .6s ease both;
   background:radial-gradient(600px 400px at 100% 0%,rgba(163,230,53,.18),transparent 60%),
              linear-gradient(150deg,#1E0B3D 0%,#3B0E8C 45%,#6D28D9 100%);border:1px solid rgba(167,139,250,.35);
   box-shadow:0 40px 90px -40px rgba(139,92,246,.95);}
.ox-auth h1{color:#fff;font-size:2.5rem;line-height:1.08;font-weight:700;margin:1.4rem 0 .7rem;max-width:430px;}
.ox-auth h1 em{font-style:normal;background:linear-gradient(90deg,#D9F99D,#A3E635);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ox-auth p{color:#DDD6FE;font-size:1rem;max-width:420px;}
.ox-auth .it{display:flex;gap:.8rem;align-items:flex-start;margin:1.05rem 0;max-width:430px;animation:ox-subir .6s ease both;}
.ox-auth .it:nth-of-type(2){animation-delay:.1s}.ox-auth .it:nth-of-type(3){animation-delay:.2s}
.ox-auth .it .b{flex:0 0 auto;width:38px;height:38px;border-radius:11px;background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;
   border:1px solid rgba(255,255,255,.16);color:#D9F99D;}
.ox-auth .it b{color:#fff;display:block;font-size:.95rem;}
.ox-auth .it span{color:#C4B5FD;font-size:.85rem;}
.ox-auth .stats{display:flex;gap:1.8rem;margin-top:1.6rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,.14);}
.ox-auth .stats b{display:block;font-size:1.6rem;color:#fff;font-family:'Space Grotesk',sans-serif;}
.ox-auth .stats span{font-size:.78rem;color:#C4B5FD;}
.ox-marca{display:flex;align-items:center;gap:.7rem;}
.ox-marca b{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;letter-spacing:-.01em;}
/* Sistema orbital animado */
.ox-sistema{position:absolute;right:-150px;bottom:-150px;width:380px;height:380px;pointer-events:none;opacity:.85;}
.ox-sistema .o{position:absolute;inset:0;border-radius:50%;border:1px solid rgba(255,255,255,.14);animation:ox-girar 22s linear infinite;}
.ox-sistema .o:nth-child(2){inset:55px;border-color:rgba(163,230,53,.28);animation-duration:15s;animation-direction:reverse;}
.ox-sistema .o:nth-child(3){inset:110px;border-color:rgba(255,255,255,.2);animation-duration:9s;}
.ox-sistema .o::before{content:"";position:absolute;top:-6px;left:50%;width:12px;height:12px;border-radius:50%;background:#A3E635;box-shadow:0 0 18px #A3E635;}
.ox-sistema .o:nth-child(2)::before{background:#22D3EE;box-shadow:0 0 18px #22D3EE;width:10px;height:10px;}
.ox-sistema .o:nth-child(3)::before{background:#F0ABFC;box-shadow:0 0 16px #F0ABFC;width:8px;height:8px;top:-4px;}
.ox-sistema .n{position:absolute;inset:160px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#C4B5FD,#7C3AED 60%,#4C1D95);
   box-shadow:0 0 50px rgba(167,139,250,.8);animation:ox-flotar 5s ease-in-out infinite;}
.ox-auth-t{font-family:'Space Grotesk',sans-serif;font-size:1.6rem;font-weight:700;color:#FAFAFA;margin:.25rem 0 .1rem;}
.ox-auth-s{color:#A1A1AA;font-size:.92rem;margin-bottom:.7rem;}
.ox-nota{display:flex;gap:.5rem;align-items:flex-start;color:#71717A;font-size:.8rem;margin-top:.7rem;}
</style>
"""


_SIN_TRADUCCION = """<script>
// Streamlit declara la página en inglés (lang="en"); el navegador ofrece traducirla y "traduce" el nombre
// de los íconos (p. ej. "science" -> "CIENCIA"). Se declara en español y se desactiva la traducción automática.
(function () {
  const d = window.parent.document;
  d.documentElement.setAttribute("lang", "es");
  d.documentElement.setAttribute("translate", "no");
  d.documentElement.classList.add("notranslate");
  if (!d.querySelector('meta[name="google"]')) {
    const m = d.createElement("meta"); m.name = "google"; m.content = "notranslate"; d.head.appendChild(m);
  }
})();
</script>"""


def _sin_traduccion() -> None:
    import streamlit.components.v1 as components
    components.html(_SIN_TRADUCCION, height=0)


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    _sin_traduccion()


def aplicar_auth() -> None:
    st.markdown(CSS_AUTH, unsafe_allow_html=True)


def esc(x) -> str:
    return _html.escape("" if x is None else str(x))


def _color(clave: str) -> str:
    return AVATAR_COLORES[int(hashlib.md5((clave or "?").encode()).hexdigest(), 16) % len(AVATAR_COLORES)]


def iniciales(nombre: str) -> str:
    p = (nombre or "?").split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()


def avatar(nombre: str, tam: int = 44) -> str:
    return (f'<div class="ox-av" style="width:{tam}px;height:{tam}px;font-size:{tam * 0.36:.0f}px;'
            f'background:linear-gradient(135deg,{_color(nombre)},{_color(nombre + "x")})">{esc(iniciales(nombre))}</div>')


def logo_empresa(nombre: str) -> str:
    c = _color(nombre)
    return f'<div class="ox-logo-emp" style="background:{c}22;color:{c}">{esc(iniciales(nombre))}</div>'


def badge_rol(rol: str) -> str:
    t, c, bg = ROL_ESTILO.get(rol, ROL_ESTILO["profesional"])
    return f'<span class="ox-badge" style="color:{c};background:{bg}">{t}</span>'


def pill(texto, clase: str = "", ic: str | None = None) -> str:
    return f'<span class="ox-pill {clase}">{icono(ic, 13) if ic else ""}{esc(texto)}</span>'


def pills(items, clase: str = "") -> str:
    """Lista de píldoras. Cada elemento puede ser texto o una tupla (icono, texto)."""
    out = []
    for i in items or []:
        out.append(pill(i[1], clase, i[0]) if isinstance(i, tuple) else pill(i, clase))
    return "".join(out)


def pills_ok(items) -> str:
    return "".join(pill(i, "ok", "check") for i in items or [])


def pills_no(items) -> str:
    return "".join(pill(i, "no", "cerrar") for i in items or [])


def anillo(pct: float, etiqueta: str | None = None) -> str:
    """Anillo de progreso SVG. El arco se anima con stroke-dashoffset (sin variables CSS, que Streamlit elimina)."""
    pct = max(0, min(100, float(pct or 0)))
    color = LIMA if pct >= 70 else VIOLETA_2 if pct >= 45 else "#FBBF24"
    return (f'<div class="ox-ring"><svg viewBox="0 0 36 36" aria-hidden="true">'
            f'<circle cx="18" cy="18" r="15.5" fill="#0F0F13" stroke="#24242A" stroke-width="3"/>'
            f'<circle class="arco" cx="18" cy="18" r="15.5" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" '
            f'pathLength="100" stroke-dasharray="100" stroke-dashoffset="{100 - pct:.1f}" transform="rotate(-90 18 18)"/></svg>'
            f'<span>{esc(etiqueta if etiqueta is not None else f"{pct:.0f}%")}</span></div>')


def barra(pct: float) -> str:
    return f'<div class="ox-bar"><i style="width:{max(0, min(100, pct)):.0f}%"></i></div>'


def encabezado(titulo: str, subtitulo: str = "", ic: str = "chispa") -> None:
    st.markdown(f'<div class="ox-head"><div class="ic">{icono(ic, 24)}</div><div><h1>{esc(titulo)}</h1>'
                f'<p>{esc(subtitulo)}</p></div></div>', unsafe_allow_html=True)


def seccion(texto: str) -> None:
    st.markdown(f'<div class="ox-sec">{esc(texto)}</div>', unsafe_allow_html=True)


_ORDEN_TONOS = ["violeta", "lima", "cian", "rosa", "naranja"]


def stat(col, valor, etiqueta: str, ic: str = "chispa", tono: str | None = None) -> None:
    tono = tono if tono in TONOS else _ORDEN_TONOS[int(hashlib.md5(etiqueta.encode()).hexdigest(), 16) % len(_ORDEN_TONOS)]
    c, bg = TONOS[tono]
    col.markdown(f'<div class="ox-stat"><div class="ico" style="background:{bg};color:{c}">{icono(ic, 21)}</div>'
                 f'<div><div class="v">{esc(valor)}</div><div class="l">{esc(etiqueta)}</div></div></div>',
                 unsafe_allow_html=True)


def vacio(ic: str, titulo: str, texto: str = "") -> None:
    st.markdown(f'<div class="ox-empty"><div class="e">{icono(ic, 26)}</div><b>{esc(titulo)}</b>{esc(texto)}</div>',
                unsafe_allow_html=True)


def tarjeta_persona(nombre: str, titular: str = "", extra_html: str = "", derecha_html: str = "", tam: int = 48) -> str:
    return (f'<div class="ox-row">{avatar(nombre, tam)}<div style="flex:1;min-width:0">'
            f'<div class="ox-t">{esc(nombre)}</div><div class="ox-s">{esc(titular)}</div>{extra_html}</div>{derecha_html}</div>')


def tarjeta_oferta(titulo: str, empresa: str, meta: list, extra_html: str = "", derecha_html: str = "") -> str:
    return (f'<div class="ox-row">{logo_empresa(empresa)}<div style="flex:1;min-width:0">'
            f'<div class="ox-t">{esc(titulo)}</div><div class="ox-s">{esc(empresa)}</div>'
            f'<div class="ox-meta">{pills(meta)}</div>{extra_html}</div>{derecha_html}</div>')


def html(contenido: str) -> None:
    st.markdown(contenido, unsafe_allow_html=True)


def pesos(valor) -> str:
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"
