"""
Testea TODOS los canales de iptv-org/argentina y genera playlist solo con los que funcionan.
"""
import re
import urllib.request
import socket
import ssl
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

M3U_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canales_iptv.m3u")

def descargar_lista():
    print("Descargando lista de iptv-org...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(M3U_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")

def parsear_m3u(contenido):
    canales = []
    lineas = contenido.strip().split("\n")
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        if linea.startswith("#EXTINF:"):
            extinf_lines = [linea]
            i += 1
            # Recoger lineas EXTVLCOPT
            while i < len(lineas) and lineas[i].strip().startswith("#EXTVLCOPT:"):
                extinf_lines.append(lineas[i].strip())
                i += 1
            # La siguiente linea es la URL
            if i < len(lineas) and not lineas[i].strip().startswith("#"):
                url = lineas[i].strip()
                # Extraer nombre
                nombre_match = re.search(r',(.+)$', extinf_lines[0])
                nombre = nombre_match.group(1).strip() if nombre_match else "Desconocido"
                canales.append({
                    "extinf_lines": extinf_lines,
                    "url": url,
                    "nombre": nombre,
                })
        i += 1
    return canales

def testear_url(canal):
    url = canal["url"]
    nombre = canal["nombre"]
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            if r.status == 200:
                return (canal, True)
            return (canal, False)
    except Exception:
        # Intentar con GET si HEAD falla
        try:
            req2 = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req2, context=ctx, timeout=8) as r:
                if r.status == 200:
                    return (canal, True)
        except Exception:
            pass
        return (canal, False)

def main():
    contenido = descargar_lista()
    canales = parsear_m3u(contenido)
    print(f"Total canales encontrados: {len(canales)}")
    print(f"Testeando todos (esto tarda ~2 minutos)...\n")

    funcionan = []
    fallan = 0
    total_testeados = 0

    with ThreadPoolExecutor(max_workers=20) as pool:
        futuros = {pool.submit(testear_url, c): c for c in canales}
        for futuro in as_completed(futuros):
            canal, ok = futuro.result()
            total_testeados += 1
            if ok:
                funcionan.append(canal)
                print(f"  [{total_testeados}/{len(canales)}] OK  {canal['nombre']}")
            else:
                fallan += 1
                print(f"  [{total_testeados}/{len(canales)}] FAIL {canal['nombre']}")

    print(f"\n{'='*50}")
    print(f"Resultados: {len(funcionan)} OK / {fallan} FAIL de {len(canales)} total")
    print(f"{'='*50}\n")

    # Generar M3U solo con los que funcionan
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for canal in funcionan:
            for linea in canal["extinf_lines"]:
                f.write(linea + "\n")
            f.write(canal["url"] + "\n")

    print(f"Playlist guardada en: {OUTPUT}")
    print(f"Canales funcionando: {len(funcionan)}")

if __name__ == "__main__":
    main()
