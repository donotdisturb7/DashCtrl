#!/usr/bin/env python3
import sys
import os
import signal
import logging
from network_discovery import NetworkDiscovery, MonitoringServer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/dashctrl_client.log'),
        logging.StreamHandler()
    ]
)

class MonitoringClient:
    def __init__(self, discovery_port=5000):
        self.discovery_port = discovery_port
        self.discovery = NetworkDiscovery(self.discovery_port)
        self.monitoring = MonitoringServer(self.discovery_port + 1)
        self.running = False
        
        # Configuration du gestionnaire de signal
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
    def start(self):
        """Démarre le service client"""
        try:
            logging.info("Démarrage du service DashCtrl...")
            self.running = True
            
            # Démarrage du service de découverte
            logging.info("Démarrage du service de découverte sur le port %d", self.discovery_port)
            self.discovery.start_server()
            
            # Démarrage du service de monitoring
            logging.info("Démarrage du service de monitoring sur le port %d", self.discovery_port + 1)
            self.monitoring.start()
            
            logging.info("Service DashCtrl démarré avec succès")
            
            # Maintient le processus en vie
            while self.running:
                signal.pause()
                
        except Exception as e:
            logging.error("Erreur lors du démarrage du service: %s", str(e))
            self.stop()
            
    def stop(self):
        """Arrête le service client"""
        logging.info("Arrêt du service DashCtrl...")
        self.running = False
        self.discovery.stop_server()
        self.monitoring.stop()
        logging.info("Service DashCtrl arrêté")
        
    def handle_signal(self, signum, frame):
        """Gère les signaux système"""
        if signum in (signal.SIGINT, signal.SIGTERM):
            logging.info("Signal d'arrêt reçu")
            self.stop()

def main():
    # Vérifie les permissions root
    if os.geteuid() != 0:
        print("Ce service doit être exécuté en tant que root")
        sys.exit(1)
        
    client = MonitoringClient()
    client.start()

if __name__ == '__main__':
    main()
