"""Genera una demo visual estática (HTML autocontenido) de NEXO SIGNAL a partir de una entrega."""
import argparse, html, json
from pathlib import Path
import pandas as pd

PALETA = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#be185d",
          "#4d7c0f", "#b45309", "#4338ca", "#0f766e", "#a21caf", "#475569", "#65a30d"]


def leer(datos: Path, entrega: Path):
    def csv(p):
        return pd.read_csv(
            p,
            engine="c",
            dtype=str,
            keep_default_na=False,
            on_bad_lines="skip",
        )
    def buscar(nombre):
        for base in (datos, entrega):
            for suf in ("", ".gz"):
                p = base / f"{nombre}{suf}"
                if p.exists():
                    return p
        raise FileNotFoundError(nombre)
    com = csv(buscar("comentarios.csv")).drop_duplicates(
        "comentario_id", keep="first"
    )
    pred = csv(entrega / "comentarios.csv")
    narr = csv(entrega / "narrativas.csv")
    cue = csv(entrega / "cuentas.csv").drop_duplicates("cuenta_id", keep="first")
    ev = None
    for p in (entrega / "evidencia" / "grupos_coordinados.csv", entrega / "grupos_coordinados.csv"):
        if p.exists():
            ev = csv(p); break
    costo = json.loads((entrega / "costo.json").read_text())
    df = com.merge(pred, on="comentario_id", how="inner").merge(cue, on="cuenta_id", how="left")
    df["narrativa"] = df["narrativa"].replace("ninguna", "")
    df["grupo"] = df["grupo"].fillna("")
    df["ts"] = pd.to_datetime(df["fecha"], utc=True, errors="coerce").dt.tz_convert("-03:00")
    df["dia"] = df["ts"].dt.floor("D")
    return df, narr, cue, ev, costo


def sparkline(serie: pd.Series, serie_org: pd.Series, dias, origen, color, w=360, h=70):
    vmax = max(1, int(serie.max()))
    n = len(dias)
    def pts(s):
        return " ".join(f"{i * w / max(1, n - 1):.1f},{h - 4 - (s.get(d, 0) / vmax) * (h - 10):.1f}"
                        for i, d in enumerate(dias))
    marca = ""
    if origen is not None and n > 1:
        dia0 = origen.floor("D")
        if dia0 in dias:
            x = dias.index(dia0) * w / (n - 1)
            marca = (f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{h}" stroke="#111" stroke-dasharray="3,3"/>'
                     f'<text x="{x + 3:.1f}" y="10" font-size="10">origen</text>')
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts(serie)}"/>'
            f'<polyline fill="none" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="4,2" points="{pts(serie_org)}"/>'
            f'{marca}</svg>')


def barra(apoya, rechaza):
    t = max(1, apoya + rechaza)
    a = 100 * apoya / t
    return (f'<div class="bar"><span style="width:{a:.1f}%;background:#16a34a"></span>'
            f'<span style="width:{100 - a:.1f}%;background:#dc2626"></span></div>'
            f'<small>{a:.0f}% apoya · {100 - a:.0f}% rechaza</small>')


def ejemplos(g, postura, k=2):
    sub = g[(g["postura"] == postura) & (g["respuesta_a"] == "")]
    sub = sub[sub["texto"].str.len().between(40, 220)]
    if sub.empty:
        return ""
    top = sub["texto"].value_counts().head(k).index
    return "".join(f"<li>{html.escape(t)}</li>" for t in top)


def render(df, narr, cue, ev, costo, titulo_set):
    e = html.escape
    dias = sorted(df["dia"].dropna().unique())
    n_total = len(df)
    n_ruido = int((df["narrativa"] == "").sum())
    coord = df["grupo"] != ""
    n_cuentas_coord = int((cue["grupo"] != "").sum())
    n_grupos = cue.loc[cue["grupo"] != "", "grupo"].nunique()
    tam = df[df["narrativa"] != ""].groupby("narrativa").size()
    narr = narr.assign(n=narr["narrativa"].map(tam).fillna(0).astype(int)).sort_values("n", ascending=False)

    filas = []
    lens = []
    for i, r in enumerate(narr.itertuples(index=False)):
        g = df[df["narrativa"] == r.narrativa]
        color = PALETA[i % len(PALETA)]
        serie = g.groupby("dia").size()
        serie_org = g[g["grupo"] == ""].groupby("dia").size()
        origen = pd.to_datetime(r.fecha_origen, errors="coerce")
        origen = origen.tz_convert("-03:00") if origen is not pd.NaT and origen is not None else None
        ap, re_ = int((g["postura"] == "apoya").sum()), int((g["postura"] == "rechaza").sum())
        inflado = int((g["grupo"] != "").sum())
        lens.append((r.narrativa, r.titulo, len(g), inflado))
        frases = " ".join(f'<span class="chip">{e(f)}</span>' for f in r.frases_clave.split("|") if f)
        filas.append(f"""
<section class="card" style="border-left:6px solid {color}">
  <div class="head"><b>{e(r.narrativa)}</b> · {e(r.titulo)}<span class="n">{len(g):,} comentarios</span></div>
  <div class="grid">
    <div>{sparkline(serie, serie_org, dias, origen, color)}
      <small>Volumen diario (línea continua: total; punteada: sin cuentas coordinadas). Origen: {e(r.fecha_origen)}</small></div>
    <div>{barra(ap, re_)}<div class="chips">{frases}</div>
      {'<p class="warn">' + f'{inflado:,} comentarios ({100 * inflado / max(1, len(g)):.1f}%) provienen de cuentas coordinadas' + '</p>' if inflado else ''}</div>
  </div>
  <details><summary>Comentarios representativos</summary>
    <div class="grid"><div><b class="ap">Apoya</b><ul>{ejemplos(g, 'apoya')}</ul></div>
    <div><b class="re">Rechaza</b><ul>{ejemplos(g, 'rechaza')}</ul></div></div></details>
</section>""")

    lens_rows = "".join(
        f"<tr><td>{e(n)}</td><td>{e(t)}</td><td>{tot:,}</td><td>{tot - inf:,}</td>"
        f"<td>{'<b>' if inf else ''}{100 * inf / max(1, tot):.1f}%{'</b>' if inf else ''}</td></tr>"
        for n, t, tot, inf in sorted(lens, key=lambda x: -x[3] / max(1, x[2])))

    grupos_html = ""
    if ev is not None and len(ev):
        for r in ev.itertuples(index=False):
            g = df[df["grupo"] == r.grupo]
            narrs = g[g["narrativa"] != ""]["narrativa"].value_counts()
            objetivo = ", ".join(f"{e(k)} ({v})" for k, v in narrs.head(3).items()) or "—"
            post = g[g["narrativa"] != ""]["postura"].value_counts(normalize=True)
            p = ", ".join(f"{k} {100 * v:.0f}%" for k, v in post.items())
            canal = {"T": "sincronía / texto repetido", "R": "red de respuestas"}.get(str(r.canal), str(r.canal))
            grupos_html += f"""
<tr><td><b>{e(r.grupo)}</b></td><td>{r.n_cuentas}</td><td>{e(canal)}</td><td>{float(r.densidad):.2f}</td>
<td>{float(r.ratio):,.0f}×</td><td>{float(r.mediana_dias_cuenta_al_primer_comentario):.0f} d</td>
<td>{float(r.frac_nocturna) * 100:.0f}%</td><td>{len(g):,}</td><td>{objetivo}<br><small>{e(p)}</small></td>
<td><i>{e(str(r.ejemplo_texto)[:120])}</i></td></tr>"""
    else:
        grupos_html = '<tr><td colspan="10">No se detectaron operaciones coordinadas.</td></tr>'

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEXO SIGNAL — {e(titulo_set)}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f8fafc;color:#0f172a}}
header{{background:#0f172a;color:#fff;padding:24px 32px}} header h1{{margin:0;font-size:26px;letter-spacing:.5px}}
header p{{margin:4px 0 0;color:#cbd5e1}} main{{max-width:1180px;margin:0 auto;padding:24px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}}
.kpi{{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px #0001}} .kpi b{{font-size:24px;display:block}}
.kpi span{{color:#64748b;font-size:13px}} h2{{margin:28px 0 12px}}
.card{{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px #0001}}
.head{{font-size:16px;margin-bottom:8px}} .n{{float:right;color:#64748b;font-size:13px}}
.grid{{display:grid;grid-template-columns:380px 1fr;gap:16px;align-items:start}}
.bar{{display:flex;height:12px;border-radius:6px;overflow:hidden;width:100%;max-width:420px}} .bar span{{display:block}}
.chip{{display:inline-block;background:#e2e8f0;border-radius:12px;padding:2px 8px;margin:3px 3px 0 0;font-size:12px}}
.warn{{color:#b45309;font-size:13px;margin:6px 0 0}} small{{color:#64748b}} .ap{{color:#16a34a}} .re{{color:#dc2626}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:10px;overflow:hidden;font-size:13px}}
th,td{{padding:8px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}} th{{background:#f1f5f9}}
details summary{{cursor:pointer;color:#2563eb;font-size:13px;margin-top:6px}} ul{{margin:6px 0;padding-left:18px;font-size:13px}}
footer{{color:#64748b;font-size:12px;text-align:center;padding:24px}}
</style></head><body>
<header><h1>NEXO SIGNAL</h1><p>Narrativas, posturas y operaciones coordinadas · {e(titulo_set)}</p></header>
<main>
<div class="kpis">
<div class="kpi"><b>{n_total:,}</b><span>comentarios analizados</span></div>
<div class="kpi"><b>{len(narr)}</b><span>narrativas detectadas</span></div>
<div class="kpi"><b>{100 * n_ruido / max(1, n_total):.1f}%</b><span>ruido (sin narrativa)</span></div>
<div class="kpi"><b>{n_grupos}</b><span>operaciones coordinadas</span></div>
<div class="kpi"><b>{n_cuentas_coord}</b><span>cuentas coordinadas</span></div>
<div class="kpi"><b>{costo.get('segundos', '—')} s</b><span>tiempo de proceso · USD {costo.get('usd_ia', 0)} IA</span></div>
</div>
<h2>Narrativas</h2>
{''.join(filas)}
<h2>Operaciones coordinadas</h2>
<table><tr><th>Grupo</th><th>Cuentas</th><th>Señal</th><th>Densidad</th><th>vs. azar</th><th>Edad cuenta al 1er comentario (mediana)</th><th>Nocturno</th><th>Comentarios</th><th>Narrativa objetivo</th><th>Ejemplo</th></tr>
{grupos_html}</table>
<h2>ORGANIC LENS — actividad total vs. orgánica</h2>
<p><small>Cuánto del volumen de cada narrativa proviene de cuentas con indicios de coordinación.</small></p>
<table><tr><th>Narrativa</th><th>Título</th><th>Total</th><th>Sin coordinadas</th><th>Inflado</th></tr>{lens_rows}</table>
</main><footer>Generado automáticamente por NEXO ENGINE a partir de la entrega · sin etiquetado manual · {e(costo.get('hardware', ''))}</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--entrega", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--titulo", default="set final")
    a = ap.parse_args()
    df, narr, cue, ev, costo = leer(a.datos, a.entrega)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(render(df, narr, cue, ev, costo, a.titulo), encoding="utf-8")
    print(a.salida)


if __name__ == "__main__":
    main()
