import socket
import threading
import json
import psutil
import time

class MonitoringService:
    """Service de surveillance qui s'exécute sur l'ordinateur à surveiller"""
    def __init__(self, port=5000):
        self.port = port
        self.running = False
        self.clients = []
        
    def start(self):
        """Démarre le service de surveillance"""
        self.running = True
        
        # Socket pour la découverte réseau
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.discovery_socket.bind(('', self.port))
        
        # Socket pour les connexions des clients
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port + 1))
        self.server_socket.listen(5)
        
        # Démarrage des threads
        threading.Thread(target=self._handle_discovery, daemon=True).start()
        threading.Thread(target=self._accept_clients, daemon=True).start()
        
    def _handle_discovery(self):
        """Gère les requêtes de découverte"""
        while self.running:
            try:
                data, addr = self.discovery_socket.recvfrom(1024)
                if data == b"DISCOVER_MONITORING_SERVER":
                    # Envoie les informations du serveur
                    hostname = socket.gethostname()
                    response = {
                        "hostname": hostname,
                        "port": self.port + 1
                    }
                    self.discovery_socket.sendto(json.dumps(response).encode(), addr)
            except Exception as e:
                print(f"Erreur découverte: {e}")
                
    def _accept_clients(self):
        """Accepte les connexions des clients"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                self.clients.append((client_socket, addr))
            except Exception as e:
                print(f"Erreur connexion: {e}")
                
    def _handle_client(self, client_socket, addr):
        """Gère la communication avec un client"""
        print(f"Nouveau client connecté: {addr}")
        try:
            while self.running:
                # Collecte des informations système
                system_info = {
                    'cpu': {
                        'percent': psutil.cpu_percent(interval=1),
                        'per_cpu': psutil.cpu_percent(percpu=True),
                        'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    },
                    'memory': psutil.virtual_memory()._asdict(),
                    'swap': psutil.swap_memory()._asdict(),
                    'disks': {
                        disk.mountpoint: psutil.disk_usage(disk.mountpoint)._asdict()
                        for disk in psutil.disk_partitions(all=False)
                    }
                }
                
                # Envoi des données
                try:
                    client_socket.send(json.dumps(system_info).encode())
                    time.sleep(1)  # Attente d'une seconde entre chaque envoi
                except:
                    break
                    
        except Exception as e:
            print(f"Erreur client {addr}: {e}")
        finally:
            client_socket.close()
            self.clients.remove((client_socket, addr))
            print(f"Client déconnecté: {addr}")
            
    def stop(self):
        """Arrête le service"""
        self.running = False
        for client_socket, _ in self.clients:
            client_socket.close()
        self.server_socket.close()
        self.discovery_socket.close()

def main():
    service = MonitoringService()
    service.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()

if __name__ == '__main__':
    main()
