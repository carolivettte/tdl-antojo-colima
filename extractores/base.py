"""Extractor ético: respeta robots.txt, se identifica y no satura sitios.

Basado en el código del Kit de arranque del proyecto TDL, con lo visto en clase:
- User-Agent en los headers (scraping estático con requests, sesión 10).
- Pausa entre peticiones y logging del avance (procesamiento por lotes).
- Manejo del 429 respetando la cabecera Retry-After (sesión 12 y sesión 41).
- Si robots.txt no existe (404) se permite el acceso, como indica el estándar;
  si responde 401/403 o no responde, se bloquea todo, que es lo conservador.
"""
import logging
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

from extractores.config import cargar_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("tdl")


def user_agent(contacto=None):
    contacto = contacto or cargar_config()["proyecto"]["contacto"]
    return f"TDL-Observatorio/1.0 (proyecto academico TecNM Colima; contacto: {contacto})"


class ExtractorEtico:
    def __init__(self, pausa=None, contacto=None):
        cfg = cargar_config()
        self.pausa = pausa if pausa is not None else cfg["proyecto"]["pausa_segundos"]
        self.ua = user_agent(contacto)
        self.headers = {"User-Agent": self.ua}
        self.robots = {}   # reglas de robots.txt por dominio
        self.ultimo = {}   # hora de la última petición por dominio

    def _reglas(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            try:
                r = requests.get(base + "/robots.txt", headers=self.headers, timeout=20)
                if r.status_code in (401, 403):
                    rp.disallow_all = True
                elif r.status_code >= 400:
                    rp.allow_all = True
                else:
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp.disallow_all = True  # sin respuesta no asumimos permiso
            logger.info(f"robots.txt de {base}: {'bloqueado' if rp.disallow_all else 'leído'}")
            self.robots[base] = rp
        return self.robots[base]

    def permitido(self, url):
        return self._reglas(url).can_fetch(self.ua, url)

    def get(self, url, params=None, intentos=3):
        reglas = self._reglas(url)
        if not reglas.can_fetch(self.ua, url):
            raise PermissionError(f"robots.txt no permite {url}")
        dominio = urlparse(url).netloc
        pausa = max(self.pausa, reglas.crawl_delay(self.ua) or 0)

        for intento in range(1, intentos + 1):
            # Pausa mínima entre peticiones al mismo sitio (no saturarlo)
            espera = pausa - (time.time() - self.ultimo.get(dominio, 0))
            if espera > 0:
                time.sleep(espera)
            try:
                resp = requests.get(url, params=params, headers=self.headers, timeout=60)
            except requests.RequestException as e:
                logger.warning(f"Intento {intento}: sin conexión ({type(e).__name__}). Reintentando...")
                self.ultimo[dominio] = time.time()
                time.sleep(pausa * 2**intento)
                continue
            self.ultimo[dominio] = time.time()

            if resp.status_code == 429:
                # Igual que en la sesión 12: respetar Retry-After o esperar un tiempo fijo
                espera = int(resp.headers.get("Retry-After", 30))
                logger.warning(f"[429] Límite alcanzado. Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
                continue
            if resp.status_code >= 500:
                logger.warning(f"[{resp.status_code}] Error del servidor. Reintentando...")
                time.sleep(pausa * 2**intento)  # espera exponencial
                continue

            resp.raise_for_status()  # lanza error si el código no es 2xx
            return resp

        raise RuntimeError(f"Sin respuesta válida de {url} tras {intentos} intentos")
