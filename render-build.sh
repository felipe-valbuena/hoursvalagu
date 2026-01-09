#!/usr/bin/env bash
# Salir si hay un error
set -o errexit

# Instalar las librerías de Python
pip install -r requirements.txt

# Descargar e instalar Chrome para que Selenium pueda funcionar en Render
STORAGE_DIR=$HOME/.render/chrome
if [ ! -d "$STORAGE_DIR" ]; then
  mkdir -p $STORAGE_DIR
  cd $STORAGE_DIR
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x google-chrome-stable_current_amd64.deb .
fi
export PATH=$PATH:$STORAGE_DIR/opt/google/chrome
