# -*- coding: utf-8 -*-
"""
Baixa a planilha de apontamento da frota do Dropbox e salva como planilha.xlsx.

NÃO processa dados nem mexe no index.html: toda a lógica do BI está no JS do
index.html, que lê a planilha.xlsx direto no navegador.

Variável de ambiente (secret do GitHub): DROPBOX_URL = link compartilhado do
ARQUIVO no Dropbox (Compartilhar > Copiar link; "qualquer pessoa com o link").
O script força dl=1 e, se o Dropbox devolver página HTML, tenta de novo pelo
host de download direto (dl.dropboxusercontent.com).
"""
import os
import sys
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DESTINO = "planilha.xlsx"


def montar(url: str, host: str = None) -> str:
    p = urlparse(url)
    q = parse_qs(p.query)
    q["dl"] = ["1"]
    q.pop("raw", None)
    q.pop("st", None)
    if host:
        p = p._replace(netloc=host)
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def baixar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bi-frota)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def eh_xlsx(dados: bytes) -> bool:
    return len(dados) >= 1000 and dados[:2] == b"PK"


def diagnostico(url: str) -> str:
    """Descreve o tipo de link sem expor a chave (rlkey)."""
    p = urlparse(url)
    caminho = p.path
    if "/scl/fo/" in caminho or "/sh/" in caminho:
        return "link de PASTA (precisa ser link do ARQUIVO .xlsx)"
    if caminho.startswith("/home") or caminho.startswith("/preview"):
        return "endereço da barra do navegador (precisa ser link de compartilhamento: Compartilhar > Copiar link)"
    if "/scl/fi/" in caminho or caminho.startswith("/s/"):
        return f"link de arquivo ({p.netloc}{caminho.split('?')[0][:12]}…) — confira se está liberado para 'qualquer pessoa com o link'"
    return f"formato não reconhecido (host {p.netloc})"


def main() -> int:
    bruto = os.environ.get("DROPBOX_URL", "").strip().strip('"').strip("'")
    if not bruto:
        print("ERRO: secret DROPBOX_URL não configurado.")
        return 1
    if not bruto.startswith("http"):
        print("ERRO: o secret DROPBOX_URL não começa com http — cole só o link, sem texto extra.")
        return 1

    tentativas = [montar(bruto), montar(bruto, "dl.dropboxusercontent.com")]
    dados = b""
    for i, url in enumerate(tentativas, 1):
        try:
            dados = baixar(url)
        except Exception as e:  # noqa: BLE001
            print(f"Tentativa {i}: falhou ({e.__class__.__name__}: {e}).")
            continue
        if eh_xlsx(dados):
            break
        print(f"Tentativa {i}: veio {len(dados):,} bytes que não são .xlsx (início {dados[:15]!r}).")
    else:
        print("ERRO: não consegui baixar um .xlsx válido.")
        print("Tipo de link no secret:", diagnostico(bruto))
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
