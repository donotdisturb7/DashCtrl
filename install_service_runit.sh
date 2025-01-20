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
RUNIT_SERVICE_DIR="/etc/runit/sv/$SERVICE_NAME"

echo "Installation du service DashCtrl pour runit..."

# Création du répertoire d'installation
mkdir -p $INSTALL_DIR
mkdir -p $RUNIT_SERVICE_DIR/log

# Copie des fichiers
cp monitoring_client.py network_discovery.py requirements.txt $INSTALL_DIR/

# Installation des dépendances Python
echo "Installation des dépendances Python..."
python3 -m venv $PYTHON_VENV
$PYTHON_VENV/bin/pip install -r $INSTALL_DIR/requirements.txt

# Création du script run pour le service
cat > $RUNIT_SERVICE_DIR/run << EOL
#!/bin/sh
exec 2>&1
exec $PYTHON_VENV/bin/python $INSTALL_DIR/monitoring_client.py
EOL

# Création du script run pour les logs
cat > $RUNIT_SERVICE_DIR/log/run << EOL
#!/bin/sh
exec svlogd -tt /var/log/$SERVICE_NAME
EOL

# Création du répertoire de logs
mkdir -p /var/log/$SERVICE_NAME

# Ajout des permissions d'exécution
chmod +x $INSTALL_DIR/monitoring_client.py
chmod +x $RUNIT_SERVICE_DIR/run
chmod +x $RUNIT_SERVICE_DIR/log/run

# Activation du service
ln -s $RUNIT_SERVICE_DIR /etc/runit/runsvdir/default/

echo "Installation terminée !"
echo "Le service est maintenant configuré et va démarrer automatiquement"
echo ""
echo "Pour vérifier l'état du service : sv status $SERVICE_NAME"
echo "Pour voir les logs : tail -f /var/log/$SERVICE_NAME/current"
echo ""
echo "Commandes utiles :"
echo "  Démarrer : sv up $SERVICE_NAME"
echo "  Arrêter : sv down $SERVICE_NAME"
echo "  Redémarrer : sv restart $SERVICE_NAME"
echo "  Voir l'état : sv status $SERVICE_NAME"
