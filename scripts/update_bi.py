# -*- coding: utf-8 -*-
"""
Baixa a planilha de apontamento da frota do Dropbox e salva como planilha.xlsx.

NÃO processa dados nem mexe no index.html: toda a lógica do BI está no JS do
index.html, que lê a planilha.xlsx direto no navegador.

Variável de ambiente (secret do GitHub): DROPBOX_URL = link compartilhado do
arquivo no Dropbox. O script força ?dl=1 para baixar o arquivo (e não a página).
"""
import os
import sys
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DESTINO = "planilha.xlsx"


def link_download(url: str) -> str:
    p = urlparse(url.strip())
    q = parse_qs(p.query)
    q["dl"] = ["1"]
    q.pop("raw", None)
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def main() -> int:
    url = os.environ.get("DROPBOX_URL", "").strip()
    if not url:
        print("ERRO: secret DROPBOX_URL não configurado.")
        return 1

    url = link_download(url)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bi-frota)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dados = r.read()

    # .xlsx é um zip: tem que começar com "PK". Se vier HTML, o link do Dropbox mudou.
    if len(dados) < 1000 or dados[:2] != b"PK":
        print(f"ERRO: o download não é um .xlsx válido ({len(dados)} bytes). "
              f"Início: {dados[:80]!r}. Confira o link do Dropbox no secret DROPBOX_URL.")
        return 1

    antigo = open(DESTINO, "rb").read() if os.path.exists(DESTINO) else b""
    if antigo == dados:
        print("Planilha sem alterações.")
        return 0

    with open(DESTINO, "wb") as f:
        f.write(dados)
    print(f"planilha.xlsx atualizada ({len(dados):,} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
