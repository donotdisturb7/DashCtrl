#!/bin/bash

# Vérifie si l'utilisateur est root
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté en tant que root"
    exit 1
fi

# Définition des variables
INSTALL_DIR="/opt/dashctrl"
SERVICE_NAME="dashctrl"
PYTHON_VENV="$INSTALL_DIR/venv"

echo "Installation du service DashCtrl..."

# Création du répertoire d'installation
mkdir -p $INSTALL_DIR

# Copie des fichiers
cp monitoring_client.py network_discovery.py requirements.txt $INSTALL_DIR/

# Installation des dépendances Python
echo "Installation des dépendances Python..."
python3 -m venv $PYTHON_VENV
$PYTHON_VENV/bin/pip install -r $INSTALL_DIR/requirements.txt

# Création du service systemd
cat > /etc/systemd/system/$SERVICE_NAME.service << EOL
[Unit]
Description=DashCtrl Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON_VENV/bin/python $INSTALL_DIR/monitoring_client.py
Restart=always
User=root
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOL

# Ajout des permissions d'exécution
chmod +x $INSTALL_DIR/monitoring_client.py

# Rechargement de systemd et activation du service
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "Installation terminée !"
echo "Le service est maintenant actif et démarrera automatiquement au démarrage du système"
echo "Pour vérifier l'état du service : systemctl status $SERVICE_NAME"
echo "Pour voir les logs : journalctl -u $SERVICE_NAME -f"
