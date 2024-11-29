#!/usr/bin/env bash
# Baixa e adiciona a chave pública do Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adiciona o repositório do Google Chrome
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Atualiza os pacotes e instala o Google Chrome
apt-get update
apt-get install -y google-chrome-stable
