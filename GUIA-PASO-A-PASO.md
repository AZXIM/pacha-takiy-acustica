# Pacha Takiy · Guía paso a paso

Todo lo que hay que hacer, en orden.

| Archivo | Para qué |
|---|---|
| `pacha-takiy-acustica.zip` | **Tu repositorio de GitHub** (página accesible + Sonic Visualiser + El Niño) |
| `pacha-takiy-completo.zip` | El proyecto completo de Ronald **con todas las mejoras**, listo para correr en tu PC |
| `parches/0001…0003.patch` | Las mejoras para subirlas al repositorio de Ronald (Pull Request) |
| `aporte-acustica-archivos.zip` | Los mismos cambios como archivos sueltos (plan B de los parches) |
| `sonic-visualiser-listo.zip` | Audios + capas + reportes para abrir ya en Sonic Visualiser |
| `DESCRIPCION-PR.md` | Texto del Pull Request |
| `FUNDAMENTO-MATEMATICO.md` | Todas las fórmulas y la lógica (para el jurado) |

---

## Paso 1 · Tu página en GitHub (GitHub Pages)

1. Entra a **github.com/new** con tu cuenta **AZXIM**. Repository name: `pacha-takiy-acustica` (si ya lo creaste, entra a él). Marca **Public** → **Create repository**.
2. Descomprime `pacha-takiy-acustica.zip`. Abre la carpeta `pacha-takiy-acustica`.
3. En GitHub, toca **uploading an existing file** (o **Add file → Upload files** si el repositorio ya existe).
4. Selecciona **todo lo que está dentro** de la carpeta (archivos y las carpetas `sonic-visualiser`, `reportes`, `datos`, `capturas`) y arrástralo a la página. Espera a que suban los WAV. GitHub acepta hasta 100 archivos por subida; si te lo pide, sube primero los archivos sueltos y luego cada carpeta.
5. Abajo escribe: `Visor accesible, El Niño y Sonic Visualiser` → **Commit changes**.
6. **Settings → Pages**. En *Build and deployment*, Source: **Deploy from a branch** → Branch: **main** y carpeta **/(root)** → **Save**.
7. Espera 1–2 minutos y abre **https://azxim.github.io/pacha-takiy-acustica/**. Arriba aparece el enlace en *Settings → Pages*.
8. La portada del repositorio (https://github.com/AZXIM/pacha-takiy-acustica) muestra el README con las dos imágenes y los resultados.

**Probar la accesibilidad:**
- **Modo Ver:** sin sonido; se ven los puntos, la llovizna, los subtítulos y el mapa.
- **Modo Escuchar:** usa el lector de pantalla (NVDA en Windows, TalkBack en Android) y las flechas `←` `→`.
- **Vibración:** abre el enlace en un **Android con Chrome** y toca "Sentir el área" o "Comparar A y B al tacto". El iPhone no vibra desde una página web.

---

## Paso 2 · Sonic Visualiser

### Qué descargar
1. **Sonic Visualiser** (gratis): https://www.sonicvisualiser.org/download.html → *Windows 64-bit installer*. Instálalo con "Siguiente, Siguiente".
2. Opcional: el **Vamp Plugin Pack** para detectar golpes automáticamente: https://www.vamp-plugins.org/pack.html
3. De este chat: **`sonic-visualiser-listo.zip`**. Descomprímelo; la carpeta `sonic_visualiser` tiene todo junto: `.sv`, `.wav` y `.csv`.

### Abrir (doble clic, sin configurar nada)
1. Doble clic en **`ab_demo.sv`**. Si Windows pregunta con qué abrirlo, elige Sonic Visualiser.
2. La primera vez sale "Welcome to Sonic Visualiser!": toca **OK**.
3. Se abre con dos paneles:
   - **Arriba:** espectrograma con cada golpe marcado ("golpe 1/2 (A 13:30)"), una mancha brillante a 440 Hz por golpe.
   - **Abajo:** la curva del rumor (dBFS) y las regiones A (25,4 %) y B (12,1 %). A está más alto: más área con lluvia, más rumor.
4. Pulsa **F** (zoom para ver todo) y **Espacio** para escuchar mientras avanza la línea.
5. **El Niño:** doble clic en **`temporadas.sv`**. Son tres paneles:
   - el espectrograma de las 44 temporadas;
   - las regiones con la lluvia de cada temporada y su etiqueta, por ejemplo "1997-98 · El Niño fuerte (ONI +2.22) · bajo lo normal";
   - la curva del **ONI de El Niño**.
   Cuando el ONI sube, la lluvia baja.
6. Comprobación independiente (con el Vamp Plugin Pack): **Transform → Analysis by Category → Onsets → Note Onset Detector**. Sus marcas caen sobre los golpes de la regla.

Las capturas `docs/sonic-visualiser-ab.png` y `docs/sonic-visualiser-el-nino.png` son de Sonic Visualiser 4.5.2 abriendo estas mismas sesiones.

Si mueves los archivos, deja cada `.sv` junto a su `.wav`. Si prefieres hacerlo a mano: **File → Open** el `.wav`, luego **Layer → Add Spectrogram** y **File → Import Annotation Layer** con los `.csv`; las columnas están en `LEEME.md`.

## Paso 3 · El proyecto completo en tu PC (Windows)

1. Descomprime `pacha-takiy-completo.zip`. Necesitas **Python 3.12 o superior**.
2. `iniciar.bat`: crea el entorno; la primera vez necesita internet.
3. `servir_web.bat` → abre http://127.0.0.1:8000/?demo (la app de Ronald).
4. `sonic_visualiser.bat`: recalcula El Niño, genera los audios y capas en `salidas\sonic_visualiser` y actualiza los reportes y el visor `docs\acustica`.
5. `probar.bat`: corre todas las pruebas (228 de Python; con Node.js, también las de la web y la captura del audio real).

---

## Paso 4 · Subir las mejoras al repositorio de Ronald (como colaboradora)

1. Acepta la invitación: https://github.com/notifications o el correo de GitHub.
2. **Opción A (Git, recomendada):**
   ```
   git clone https://github.com/ronald005s/pacha-takiy.git
   cd pacha-takiy
   git checkout -b aporte/acustica-sonic-visualiser
   git am ruta\a\parches\*.patch
   git push -u origin aporte/acustica-sonic-visualiser
   ```
3. **Opción B (sin Git):** en el repositorio de Ronald, cambia a una rama nueva (botón de ramas → escribe `aporte/acustica-sonic-visualiser` → *Create branch*). Luego **Add file → Upload files** con el contenido de `aporte-acustica-archivos.zip`, respetando las carpetas.
4. En GitHub aparece **Compare & pull request**. Pega el texto de `DESCRIPCION-PR.md` → **Create pull request**.
5. Si `git am` falla porque Ronald cambió algo hoy, usa la opción B o `git am --3way`.
6. Opcional: para publicar el visor desde su repositorio, Ronald activa **Settings → Pages → main / docs**. En repositorios privados, GitHub Pages requiere un plan de pago; por eso tu repositorio público es el camino rápido.

No subas el código completo de Ronald a un repositorio público sin preguntarle: su repositorio es privado. Tu repositorio solo tiene la verificación, el visor y los datos públicos de NASA y NOAA.

---

## Paso 5 · Qué decir en la presentación (60 s)

1. **Gancho (5 s):** "La Tierra canta, y hoy canta El Niño."
2. **Persona (10 s):** un agricultor de Carumas y una persona sordociega que no pueden usar un mapa de colores.
3. **Demo (20 s):** el visor en modo Ver con el mapa: "llueve al noreste, en la cuenca alta". Luego "Comparar A y B al tacto" en el celular.
4. **Ciencia (15 s):** Sonic Visualiser con `temporadas.wav` y la curva del ONI: "4 de 5 El Niño fuertes trajeron temporadas secas a Moquegua; hoy hay un El Niño muy fuerte; la historia de NASA espera una temporada bajo lo normal".
5. **Rigor (5 s):** "Verificamos que cada sonido es el dato: ±0,17 dB; la respuesta A/B tiene un intervalo de confianza del 95 % que no incluye cero; todo está en el fundamento matemático."
6. **Cierre (5 s):** el equipo Ayni Orbital.

---

## Fuentes
- NASA GPM IMERG vía NASA GIBS (`IMERG_Precipitation_Rate_30min`), 10/02/2025.
- NASA POWER v2.10, mensual, `PRECTOTCORR` (MERRA-2), 1981–2025.
- NOAA CPC, Oceanic Niño Index y ENSO Diagnostic Discussion del 12/11/2026.
- ENFEN, Comunicado Oficial N.° 20-2026 (13/11/2026).
- INEI, límites provinciales, vía github.com/juaneladio/peru-geojson.
