"""
Genera playlist IPTV filtrada con canales específicos solicitados por el usuario y los ordena según sus preferencias.
"""
import re
import urllib.request
import os

M3U_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canales_iptv.m3u")

def descargar_lista():
    import ssl
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
            # Reemplazar Undefined por General
            linea = linea.replace('group-title="Undefined"', 'group-title="General"')
            
            extinf_lines = [linea]
            i += 1
            while i < len(lineas) and lineas[i].strip().startswith("#EXTVLCOPT:"):
                extinf_lines.append(lineas[i].strip())
                i += 1
            if i < len(lineas) and not lineas[i].strip().startswith("#"):
                url = lineas[i].strip()
                nombre_match = re.search(r',(.+)$', extinf_lines[0])
                nombre = nombre_match.group(1).strip() if nombre_match else "Desconocido"
                canales.append({
                    "extinf_lines": extinf_lines,
                    "url": url,
                    "nombre": nombre,
                })
        i += 1
    return canales

def obtener_prioridad(nombre):
    nombre_lower = nombre.lower()
    
    if "canal 9 res" in nombre_lower:
        return 1
    elif "canal 7 neuqu" in nombre_lower:
        return 2
    elif "corriente" in nombre_lower:
        return 3
    elif "disney" in nombre_lower:
        return 4
    elif "sony" in nombre_lower:
        return 5
    elif "canal 7" in nombre_lower: # Atrapa canales 70, 72, 79
        return 6
    else:
        return 7 # El resto (A24, etc)

def main():
    contenido = descargar_lista()
    canales = parsear_m3u(contenido)
    
    # Palabras clave solicitadas
    keywords = [
        "a24",
        "canal 9 res",
        "canal 7 neuqu",
        "corriente",
        "next tv",
        "disney",
        "sony",
        "canal 7", # Esto incluye Canal 70 y pico, Canal 79, etc
    ]
    
    # Canales a excluir (solicitado por el usuario)
    exclusions = [
        "telenord corrientes",
        "canal 7 salta",
        "canal 7 santiago del estero",
        "canal 79 puan",
        "canal 79 villa maza",
        "5tv corrientes",
        "tv canal 72"
    ]
    
    filtrados = []
    vistos = set()
    
    for c in canales:
        nombre_lower = c["nombre"].lower()
        id_lower = c["extinf_lines"][0].lower()
        
        # Verificar exclusiones primero
        excluded = False
        for ex in exclusions:
            if ex in nombre_lower or ex in id_lower:
                excluded = True
                break
                
        if excluded:
            continue
        
        match = False
        for kw in keywords:
            if kw in nombre_lower or kw in id_lower:
                match = True
                break
        
        if match and c["url"] not in vistos:
            filtrados.append(c)
            vistos.add(c["url"])

    # Ordenar los canales usando la función de prioridad
    filtrados.sort(key=lambda x: (obtener_prioridad(x["nombre"]), x["nombre"]))

    print(f"\nGenerando M3U con {len(filtrados)} canales en el orden solicitado...")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in filtrados:
            print(f"[{obtener_prioridad(c['nombre'])}] {c['nombre']}")
            for line in c["extinf_lines"]:
                f.write(line + "\n")
            f.write(c["url"] + "\n")
            
    print(f"\nPlaylist guardada en: {OUTPUT}")

if __name__ == "__main__":
    main()
