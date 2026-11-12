#!/usr/bin/env bash
set -euo pipefail

destino="datos/final"
repositorio="qualydata-org/desafio-qualydata"
release="set-final"
assets=(
  "fuentes.csv"
  "publicaciones.csv.gz"
  "comentarios.csv.gz"
  "cuentas.csv.gz"
)

mkdir -p "$destino"
if command -v gh >/dev/null 2>&1; then
  if gh release download set-final -R qualydata-org/desafio-qualydata -D datos/final --clobber; then
    exit 0
  fi
  echo "No se pudo descargar con gh; intentando los assets públicos con curl." >&2
fi

base="https://github.com/${repositorio}/releases/download/${release}"
for asset in "${assets[@]}"; do
  curl --fail --location --retry 2 --output "${destino}/${asset}" "${base}/${asset}"
done
