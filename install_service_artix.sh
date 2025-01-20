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

echo "Installation du service DashCtrl pour Artix Linux..."

# Installation des dépendances système si nécessaire
if ! command -v python3 &> /dev/null; then
    echo "Installation de Python..."
    pacman -S --noconfirm python python-pip
fi

# Création du répertoire d'installation
mkdir -p $INSTALL_DIR

# Copie des fichiers
cp monitoring_client.py network_discovery.py requirements.txt $INSTALL_DIR/

# Installation des dépendances Python
echo "Installation des dépendances Python..."
python3 -m venv $PYTHON_VENV
$PYTHON_VENV/bin/pip install -r $INSTALL_DIR/requirements.txt

# Création du script de service OpenRC
cat > /etc/init.d/$SERVICE_NAME << EOL
#!/sbin/openrc-run

name="DashCtrl Monitoring Service"
description="Service de monitoring système pour DashCtrl"
command="$PYTHON_VENV/bin/python"
command_args="$INSTALL_DIR/monitoring_client.py"
command_background="yes"
pidfile="/run/\${RC_SVCNAME}.pid"
output_log="/var/log/\${RC_SVCNAME}.log"
error_log="/var/log/\${RC_SVCNAME}.err"
directory="$INSTALL_DIR"

depend() {
    need net
    after network
}

start_pre() {
    checkpath -f -m 0644 -o root:root "\$output_log"
    checkpath -f -m 0644 -o root:root "\$error_log"
}
EOL

# Ajout des permissions d'exécution
chmod +x $INSTALL_DIR/monitoring_client.py
chmod +x /etc/init.d/$SERVICE_NAME

# Création du répertoire pour les logs s'il n'existe pas
touch /var/log/$SERVICE_NAME.log
touch /var/log/$SERVICE_NAME.err
chmod 644 /var/log/$SERVICE_NAME.log
chmod 644 /var/log/$SERVICE_NAME.err

# Ajout du service au démarrage et démarrage
rc-update add $SERVICE_NAME default
rc-service $SERVICE_NAME start

echo "Installation terminée !"
echo "Le service est maintenant actif et démarrera automatiquement au démarrage du système"
echo "Pour vérifier l'état du service : rc-service $SERVICE_NAME status"
echo "Pour voir les logs : tail -f /var/log/$SERVICE_NAME.log"
echo "Pour voir les erreurs : tail -f /var/log/$SERVICE_NAME.err"
echo ""
echo "Commandes utiles :"
echo "  Démarrer : rc-service $SERVICE_NAME start"
echo "  Arrêter : rc-service $SERVICE_NAME stop"
echo "  Redémarrer : rc-service $SERVICE_NAME restart"
