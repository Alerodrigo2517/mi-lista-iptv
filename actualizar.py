"""
Script de actualización automática de playlist IPTV.
Ejecutado por GitHub Actions cada 6 horas.

- Resuelve YouTube Live → m3u8 directo con yt-dlp
- Incluye canales con stream directo fijo
- Genera canales_iptv.m3u actualizado
"""

import subprocess
import sys
import os
from datetime import datetime, timezone

# ============================================================
# CANALES CON YOUTUBE LIVE (se resuelven automáticamente)
# ============================================================
CANALES_YOUTUBE = [
    {
        "nombre": "TN - Todo Noticias (YT)",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/vFwPhPS.png",
        "youtube_url": "https://www.youtube.com/live/cb12KmMMDJA",
    },
    {
        "nombre": "La Nacion (YT)",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/Gj1kqH5.png",
        "youtube_url": "https://www.youtube.com/live/FEWZjXJ7M0c",
    },
    {
        "nombre": "Telefe (YT)",
        "grupo": "Generales",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Telefe_%28nuevo_logo%29.png/960px-Telefe_%28nuevo_logo%29.png",
        "youtube_url": "https://www.youtube.com/live/XhAYcYpPzTc",
    },
    {
        "nombre": "A24 (YT)",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/LnXQkIU.png",
        "youtube_url": "https://www.youtube.com/live/ArKbAx1K-2U",
    },
    {
        "nombre": "C5N (YT)",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/dC9SZlv.png",
        "youtube_url": "https://www.youtube.com/live/xWG-47NFsTg",
    },
]

# ============================================================
# CANALES CON STREAM DIRECTO (no cambian)
# ============================================================
CANALES_DIRECTOS = [
    {
        "nombre": "TN - Todo Noticias",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/vFwPhPS.png",
        "url": "https://live-01-01-tn.vodgc.net/TN24/index_TN24_1080.m3u8",
    },
    {
        "nombre": "La Nacion +",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/Gj1kqH5.png",
        "url": "http://200.91.32.158:8080/lnmas/index.m3u8",
    },
    {
        "nombre": "A24",
        "grupo": "Noticias",
        "logo": "https://i.imgur.com/LnXQkIU.png",
        "url": "https://g5.vxral-slo.transport.edge-access.net/a12/ngrp:a24-100056_all/playlist.m3u8?sense=true",
    },
    {
        "nombre": "Canal 26",
        "grupo": "Noticias",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Canal_26_logo_%282022%29.svg/500px-Canal_26_logo_%282022%29.svg.png",
        "url": "https://stream-gtlc.telecentro.net.ar/hls/canal26hls/main.m3u8",
    },
    {
        "nombre": "Canal E",
        "grupo": "Noticias",
        "logo": "https://i.ibb.co/y4pkxH3/Qtc8-M2-PG-400x400.jpg",
        "url": "https://unlimited1-us.dps.live/perfiltv/perfiltv.smil/playlist.m3u8",
    },
    {
        "nombre": "Telefe",
        "grupo": "Generales",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Telefe_%28nuevo_logo%29.png/960px-Telefe_%28nuevo_logo%29.png",
        "url": "http://playcom.trapemn.tv:1935/transcoderip/telefe.stream/playlist.m3u8",
    },
    {
        "nombre": "El Trece",
        "grupo": "Generales",
        "logo": "https://i.imgur.com/TrgBAdA.png",
        "url": "https://livetrx01.vodgc.net/eltrecetv/index.m3u8",
    },
    {
        "nombre": "America TV",
        "grupo": "Generales",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png/500px-Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png",
        "url": "http://playcom.trapemn.tv:1935/transcoderip/america.stream/playlist.m3u8",
    },
    {
        "nombre": "El Nueve",
        "grupo": "Generales",
        "logo": "https://i.imgur.com/cJHP7bU.png",
        "url": "http://playcom.trapemn.tv:1935/transcoderip/canal9.stream/playlist.m3u8",
    },
    {
        "nombre": "NET TV",
        "grupo": "Generales",
        "logo": "https://i.imgur.com/IhJ0BjF.png",
        "url": "http://45.134.141.161:2200/ARG/Net_TV/index.m3u8",
    },
    {
        "nombre": "TyC Sports",
        "grupo": "Deportes",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/TyC_Sports_logo.svg/960px-TyC_Sports_logo.svg.png",
        "url": "http://45.181.87.106/TYCSPORTSHD/index.m3u8",
    },
    {
        "nombre": "DeporTV",
        "grupo": "Deportes",
        "logo": "https://i.imgur.com/THk9ARS.png",
        "url": "https://edgectc.com/DEPORTES_CTC_PLUS/index.m3u8",
    },
    {
        "nombre": "MusicTop",
        "grupo": "Musica",
        "logo": "https://cdn.mitvstatic.com/channels/ar_musictop_m.png",
        "url": "https://stream-gtlc.telecentro.net.ar/hls/musictophls/0/playlist.m3u8",
    },
    {
        "nombre": "Cine.Ar",
        "grupo": "Peliculas",
        "logo": "https://i.imgur.com/Iozv4tT.png",
        "url": "http://200.91.32.158:8080/cinear/index.m3u8",
    },
]

ARCHIVO_SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canales_iptv.m3u")


def log(msg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {msg}")


def resolver_youtube(youtube_url):
    """Resuelve YouTube Live → stream directo m3u8."""
    try:
        log(f"  🔄 Resolviendo: {youtube_url}")
        resultado = subprocess.run(
            ["yt-dlp", "--get-url", "-f", "best", "--no-warnings", youtube_url],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if resultado.returncode == 0 and resultado.stdout.strip():
            url = resultado.stdout.strip().split("\n")[0]
            log(f"  ✅ OK")
            return url
        else:
            log(f"  ❌ Error: {resultado.stderr.strip()[:150]}")
            return None
    except subprocess.TimeoutExpired:
        log(f"  ❌ Timeout")
        return None
    except Exception as e:
        log(f"  ❌ {e}")
        return None


def generar_m3u(canales):
    """Genera el archivo M3U."""
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lineas = [
        "#EXTM3U",
        f"# Actualizado automáticamente: {ahora}",
        f"# Total canales: {len(canales)}",
        "",
    ]
    for canal in canales:
        extinf = (
            f'#EXTINF:-1 tvg-name="{canal["nombre"]}" '
            f'tvg-logo="{canal["logo"]}" '
            f'group-title="{canal["grupo"]}",{canal["nombre"]}'
        )
        lineas.append(extinf)
        lineas.append(canal["url"])
        lineas.append("")

    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    log(f"📁 Guardado en: {ARCHIVO_SALIDA}")


def main():
    log("=" * 50)
    log("🚀 Actualización automática de playlist IPTV")
    log("=" * 50)

    canales_finales = []

    # 1. Canales YouTube
    log(f"\n📺 Resolviendo {len(CANALES_YOUTUBE)} canales de YouTube...")
    for canal in CANALES_YOUTUBE:
        url = resolver_youtube(canal["youtube_url"])
        if url:
            canales_finales.append({
                "nombre": canal["nombre"],
                "grupo": canal["grupo"],
                "logo": canal["logo"],
                "url": url,
            })

    # 2. Canales directos
    log(f"\n📡 Agregando {len(CANALES_DIRECTOS)} streams directos...")
    for canal in CANALES_DIRECTOS:
        canales_finales.append(canal.copy())
        log(f"  ✅ {canal['nombre']}")

    # 3. Generar M3U
    log(f"\n📝 Generando playlist con {len(canales_finales)} canales...")
    generar_m3u(canales_finales)

    log(f"\n✅ ¡Listo! {len(canales_finales)} canales en la playlist")


if __name__ == "__main__":
    main()
