#!/bin/bash
# generates a self-signed SSL cert for HTTPS on the pi
# run this once, then start the server with --ssl flags

mkdir -p certs

openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes \
    -subj "/C=US/ST=Local/L=Local/O=HERMES/CN=raspberrypi"

echo ""
echo "done - certs are in backend/certs/"
echo "start the server with:"
echo "  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem"
echo ""
echo "your browser will show a security warning since its self-signed - thats normal, just click through it"
