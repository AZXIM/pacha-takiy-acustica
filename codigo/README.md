# Source code · Pacha Takiy acoustic, El Niño and 3D modules

Team Ayni Orbital · NASA Space Apps Challenge 2026 · The Earth Information Jukebox

These are the modules we added to Pacha Takiy. The live page at https://azxim.github.io/pacha-takiy-acustica/ is built from them.

- `scripts/modelo_acustico.py`: mathematical model of the sound rule. AMS rain classes become 2, 4 or 7 tones at 440 Hz, and a band-pass rumble grows with rain coverage. It also includes the psychoacoustic checks.
- `scripts/analisis_acustico.py`: Goertzel tone detector. It compares real browser audio with the model.
- `scripts/sonic_visualiser.py` and `scripts/sesion_sonic_visualiser.py`: write the WAV files, CSV/Audacity labels and Sonic Visualiser sessions.
- `scripts/enso_moquegua.py`: 44 rainy seasons from NASA POWER (MERRA-2) compared with the NOAA Oceanic Niño Index, using permutation tests and cross-validation.
- `scripts/geografia.py`: where it rains inside the NASA GPM IMERG 10 × 10 grid over Moquegua.
- `scripts/terreno_3d.py`: relief of Moquegua from NASA SRTM, via AWS Terrain Tiles.
- `pruebas/python/`: automated tests (pytest). `pruebas/reportes/`: generated reports.
- `datos/mapa/`: elevation grid and province boundaries (INEI).

The scripts read the sound constants from the team's main app (`web/js/reglas.js` and `web/js/audio.js`), which lives in the team's private repository. Without those files, the tests that compare against the app are skipped.

**Use of SI:** this code was developed with help from Claude (Anthropic) and ChatGPT (OpenAI), and the team reviewed and tested it.
