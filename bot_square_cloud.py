#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BOT WORDPRESS SQUARE CLOUD
Publica artigos automaticamente no WordPress
Pronto pra Square Cloud
"""

import os
import time
import random
import requests
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO (Square Cloud)
# ============================================================================

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://financasdozero.com")
WORDPRESS_USER = os.getenv("WORDPRESS_USER", "seu_usuario")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD", "sua_senha")
DEFAULT_CATEGORY = int(os.getenv("DEFAULT_CATEGORY", "1"))
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL", "15"))
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL", "120"))

# Pasta de artigos
ARTICLES_FOLDER = "/root/artigos"
Path(ARTICLES_FOLDER).mkdir(parents=True, exist_ok=True)
Path("/root/publicados").mkdir(parents=True, exist_ok=True)

LOG_FILE = "/root/bot.log"

# ============================================================================
# BOT
# ============================================================================

class BotWordPress:
    def __init__(self):
        self.folder = Path(ARTICLES_FOLDER)
        self.url = WORDPRESS_URL.rstrip('/')
        self.user = WORDPRESS_USER
        self.pass_ = WORDPRESS_PASSWORD
        self.cat = DEFAULT_CATEGORY
        self.publicados = set()
        
        self.log("=" * 70)
        self.log("🤖 BOT WORDPRESS SQUARE CLOUD INICIADO")
        self.log("=" * 70)
        self.log(f"🌐 Site: {self.url}")
        self.log(f"📁 Pasta: {self.folder}")
        self.log(f"⏰ Intervalo: {MIN_INTERVAL}-{MAX_INTERVAL} min")
        self.log("=" * 70)
    
    def log(self, msg):
        """Escreve log"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        texto = f"[{ts}] {msg}"
        print(texto)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(texto + "\n")
        except:
            pass
    
    def conectar(self):
        """Testa conexão"""
        try:
            auth = (self.user, self.pass_)
            url = f"{self.url}/wp-json/wp/v2/users/me"
            r = requests.get(url, auth=auth, timeout=10)
            
            if r.status_code == 200:
                self.log("✅ CONEXÃO OK!")
                return True
            else:
                self.log(f"❌ Status {r.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}")
            return False
    
    def pegar_artigos(self):
        """Pega artigos não publicados"""
        try:
            files = list(self.folder.glob("*.txt")) + list(self.folder.glob("*.md"))
            novos = [f for f in files if f.name not in self.publicados]
            return sorted(novos)
        except:
            return []
    
    def ler_artigo(self, path):
        """Lê arquivo"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            linhas = conteudo.split("\n")
            titulo = ""
            categoria = self.cat
            texto = ""
            
            parse = False
            
            for linha in linhas:
                if linha.startswith("TÍTULO:"):
                    titulo = linha.replace("TÍTULO:", "").strip()
                elif linha.startswith("CATEGORIA:"):
                    try:
                        categoria = int(linha.replace("CATEGORIA:", "").strip())
                    except:
                        categoria = self.cat
                elif linha.startswith("CONTEÚDO:"):
                    parse = True
                elif parse:
                    texto += linha + "\n"
            
            if not titulo:
                titulo = path.stem.replace("_", " ")
            
            if not texto:
                texto = conteudo
            
            return {
                "title": titulo.strip(),
                "content": texto.strip(),
                "category": categoria
            }
        except Exception as e:
            self.log(f"❌ Erro ao ler: {str(e)}")
            return None
    
    def publicar(self, dados):
        """Publica artigo"""
        try:
            auth = (self.user, self.pass_)
            url = f"{self.url}/wp-json/wp/v2/posts"
            
            payload = {
                "title": dados["title"],
                "content": dados["content"],
                "status": "publish",
                "categories": [dados["category"]],
                "comment_status": "open",
                "ping_status": "open"
            }
            
            r = requests.post(url, json=payload, auth=auth, timeout=30)
            
            if r.status_code in [200, 201]:
                pid = r.json().get("id")
                self.log(f"✅ PUBLICADO: '{dados['title'][:50]}...' (ID: {pid})")
                return True
            else:
                self.log(f"❌ Erro: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}")
            return False
    
    def intervalo_aleatorio(self):
        """Intervalo aleatório"""
        return random.randint(MIN_INTERVAL, MAX_INTERVAL)
    
    def rodar(self):
        """Roda infinitamente"""
        if not self.conectar():
            self.log("⚠️  Tentando novamente em 30s...")
            time.sleep(30)
            return self.rodar()
        
        iteracao = 0
        
        while True:
            try:
                iteracao += 1
                hora = datetime.now().strftime("%H:%M:%S")
                self.log(f"\n📍 Iteração #{iteracao} - {hora}")
                
                artigos = self.pegar_artigos()
                
                if artigos:
                    self.log(f"📄 {len(artigos)} artigo(s)")
                    
                    arquivo = random.choice(artigos)
                    self.log(f"📝 Processando: {arquivo.name}")
                    
                    dados = self.ler_artigo(arquivo)
                    
                    if dados:
                        if self.publicar(dados):
                            self.publicados.add(arquivo.name)
                            
                            try:
                                pub_folder = Path("/root/publicados")
                                arquivo.rename(pub_folder / arquivo.name)
                                self.log("📁 Arquivado")
                            except:
                                pass
                    
                    intervalo = self.intervalo_aleatorio()
                    self.log(f"⏰ Próxima em {intervalo}min")
                
                else:
                    self.log("⏳ Nenhum artigo")
                    self.log("💡 Coloque em: /root/artigos/")
                    intervalo = 5
                
                time.sleep(intervalo * 60)
                
            except KeyboardInterrupt:
                self.log("\n⏹️  Parado")
                break
            except Exception as e:
                self.log(f"❌ Erro: {str(e)}")
                self.log("⏰ Tentando em 5min...")
                time.sleep(5 * 60)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    bot = BotWordPress()
    bot.rodar()
