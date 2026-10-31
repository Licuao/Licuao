"""Genera etiqueta.svg: la etiqueta de despacho que encabeza el perfil.

Lee de la API de GitHub la fecha del último día con contribuciones y el total del año,
y los imprime en la etiqueta. Solo usa la biblioteca estándar.

Uso:
    GITHUB_TOKEN=... python scripts/etiqueta.py
Sin token, la etiqueta se genera con guiones en los datos en vivo.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import urllib.request

USUARIO = "Licuao"
SALIDA = pathlib.Path(__file__).resolve().parent.parent / "etiqueta.svg"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Code 128-B de "github.com/Licuao" (1 = barra, 0 = espacio), generado con python-barcode 0.16.
CODIGO = (
    "1101001000010011010000100001101001001111010010011000010100111100101001000011010011001110"
    "1000010110010001111010111101110101011100110010001101110100001101001000010110010011110010"
    "1001011000010001111010100011011101100011101011"
)

COLORES = {
    "rack": "#0E4F8C",       # azul de los parantes del rack
    "parante": "#0A3D6E",
    "perforacion": "#072C50",
    "viga": "#F26419",       # naranja de la viga de carga
    "viga_borde": "#C94E12",
    "caja": "#C8995F",       # cartón kraft
    "caja_lado": "#B4864F",
    "cinta": "#DDB683",
    "papel": "#FFFFFF",
    "tinta": "#111111",
    "laser": "#FF2B2B",
}


def consultar(token: str) -> tuple[str, str]:
    hoy = dt.datetime.now(dt.timezone.utc)
    inicio = dt.datetime(hoy.year, 1, 1, tzinfo=dt.timezone.utc)
    consulta = """
    query($login: String!, $desde: DateTime!, $hasta: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $desde, to: $hasta) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    cuerpo = json.dumps({
        "query": consulta,
        "variables": {"login": USUARIO, "desde": inicio.isoformat(), "hasta": hoy.isoformat()},
    }).encode()
    pedido = urllib.request.Request(
        "https://api.github.com/graphql",
        data=cuerpo,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as respuesta:
        datos = json.load(respuesta)
    if "errors" in datos:
        raise RuntimeError(datos["errors"])

    calendario = datos["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    dias = [d for semana in calendario["weeks"] for d in semana["contributionDays"] if d["contributionCount"]]
    ultimo = "—"
    if dias:
        fecha = dt.date.fromisoformat(max(d["date"] for d in dias))
        ultimo = f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}"
    total = f"{calendario['totalContributions']:,}".replace(",", ".")
    return ultimo, total


def barras(x: float, y: float, alto: float, ancho_modulo: float) -> str:
    rects, i = [], 0
    while i < len(CODIGO):
        if CODIGO[i] == "1":
            j = i
            while j < len(CODIGO) and CODIGO[j] == "1":
                j += 1
            rects.append(f'<rect x="{x + i * ancho_modulo:.1f}" y="{y}" width="{(j - i) * ancho_modulo:.1f}" height="{alto}"/>')
            i = j
        else:
            i += 1
    return "".join(rects)


def perforaciones(x: float) -> str:
    return "".join(
        f'<rect x="{x}" y="{y}" width="12" height="20" rx="2"/>' for y in range(18, 430, 36)
    )


def svg(ultimo: str, total: str, anio: int) -> str:
    c = COLORES
    fuente = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 440" width="1200" height="440" role="img" aria-labelledby="t">
<title id="t">Etiqueta de despacho de Ignacio Guacte: datos, automatización y apps. Último despacho {ultimo}, {total} contribuciones en {anio}.</title>
<style>
  text {{ font-family: {fuente}; fill: {c['tinta']}; }}
  .laser {{ animation: barrido 2.6s ease-in-out infinite alternate; }}
  @keyframes barrido {{ from {{ transform: translateY(0); }} to {{ transform: translateY(34px); }} }}
  @media (prefers-reduced-motion: reduce) {{ .laser {{ animation: none; opacity: 0; }} }}
</style>

<rect width="1200" height="440" fill="{c['rack']}"/>

<!-- parantes del rack -->
<rect x="0" y="0" width="52" height="440" fill="{c['parante']}"/>
<rect x="1148" y="0" width="52" height="440" fill="{c['parante']}"/>
<g fill="{c['perforacion']}">{perforaciones(20)}{perforaciones(1168)}</g>

<!-- viga de carga -->
<rect x="52" y="372" width="1096" height="40" fill="{c['viga']}"/>
<rect x="52" y="404" width="1096" height="8" fill="{c['viga_borde']}"/>

<!-- caja principal -->
<rect x="84" y="20" width="760" height="352" fill="{c['caja']}"/>
<rect x="420" y="20" width="88" height="70" fill="{c['cinta']}"/>

<!-- etiqueta -->
<g transform="rotate(-1.2 464 202)">
  <rect x="124" y="56" width="680" height="292" fill="{c['papel']}"/>
  <text x="148" y="88" font-size="19">De: Ignacio Guacte · Chile</text>
  <rect x="744" y="56" width="60" height="48" fill="{c['tinta']}"/>
  <text x="774" y="91" font-size="28" font-weight="700" text-anchor="middle" style="fill:{c['papel']}">CL</text>
  <rect x="124" y="103" width="680" height="4" fill="{c['tinta']}"/>

  <text x="146" y="164" font-size="56" font-weight="700" letter-spacing="-1.5">Ignacio Guacte</text>
  <text x="148" y="199" font-size="24">Datos, automatización y apps</text>
  <rect x="124" y="214" width="680" height="4" fill="{c['tinta']}"/>

  <text x="148" y="240" font-size="17">Contenido</text>
  <text x="148" y="267" font-size="21" font-weight="700">Python · Kotlin · SQL</text>
  <text x="400" y="240" font-size="17">Último despacho</text>
  <text x="400" y="267" font-size="21" font-weight="700">{ultimo}</text>
  <text x="600" y="240" font-size="17">Contribuciones {anio}</text>
  <text x="600" y="267" font-size="21" font-weight="700">{total}</text>
  <rect x="124" y="280" width="680" height="4" fill="{c['tinta']}"/>

  <g fill="{c['tinta']}">{barras(148, 294, 38, 2)}</g>
  <rect class="laser" x="138" y="295" width="466" height="2" fill="{c['laser']}"/>
  <text x="620" y="320" font-size="19" font-weight="700">github.com/Licuao</text>
</g>

<!-- caja chica con este lado arriba -->
<rect x="892" y="236" width="200" height="136" fill="{c['caja_lado']}"/>
<g fill="{c['tinta']}">
  <path d="M928 312 L942 290 L956 312 Z"/><rect x="938" y="311" width="8" height="22"/>
  <path d="M964 312 L978 290 L992 312 Z"/><rect x="974" y="311" width="8" height="22"/>
  <rect x="924" y="340" width="72" height="5"/>
</g>

<!-- el gato -->
<g fill="{c['tinta']}">
  <ellipse cx="1004" cy="196" rx="40" ry="42"/>
  <circle cx="972" cy="148" r="26"/>
  <path d="M952 132 L948 102 L970 124 Z"/>
  <path d="M978 124 L994 102 L996 132 Z"/>
  <path d="M1038 226 C1076 232 1086 198 1064 176" fill="none" stroke="{c['tinta']}" stroke-width="12" stroke-linecap="round"/>
</g>
<circle cx="961" cy="146" r="4" fill="{c['viga']}"/>
</svg>
"""


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    ultimo, total = consultar(token) if token else ("—", "—")
    anio = dt.datetime.now(dt.timezone.utc).year
    SALIDA.write_text(svg(ultimo, total, anio), encoding="utf-8")
    print(f"{SALIDA.name}: último despacho {ultimo}, {total} contribuciones en {anio}")


if __name__ == "__main__":
    main()
