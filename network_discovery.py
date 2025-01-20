import socket
import json
import threading
import psutil
import platform
from datetime import datetime
import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget

class NetworkDiscovery:
    def __init__(self, port=5000):
        self.port = port
        self.running = False
        self.clients = {}  # {hostname: (address, port)}
        
    def start_server(self):
        """Démarre le serveur de découverte"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.server_socket.bind(('', self.port))
        
        # Thread pour écouter les broadcasts
        threading.Thread(target=self._listen_for_broadcasts, daemon=True).start()
        
    def stop_server(self):
        """Arrête le serveur"""
        self.running = False
        self.server_socket.close()
        
    def _listen_for_broadcasts(self):
        """Écoute les broadcasts de découverte"""
        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(1024)
                if data == b"DISCOVER_MONITORING_SERVER":
                    # Envoie les informations du système
                    response = {
                        'hostname': platform.node(),
                        'port': self.port + 1,  # Port pour la connexion TCP
                        'os': platform.system(),
                        'version': platform.version()
                    }
                    self.server_socket.sendto(
                        json.dumps(response).encode(),
                        addr
                    )
            except Exception as e:
                print(f"Erreur broadcast: {e}")
                
    def discover_clients(self, timeout=2):
        """Découvre les clients sur le réseau"""
        discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discover_socket.settimeout(1)
        
        # Envoie une requête broadcast
        discover_socket.sendto(b"DISCOVER_MONITORING_SERVER", ('<broadcast>', self.port))
        
        # Attend les réponses
        clients = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = discover_socket.recvfrom(1024)
                info = json.loads(data.decode())
                clients.append({
                    'hostname': info['hostname'],
                    'address': addr[0],
                    'port': info['port'],
                    'os': info.get('os', 'Unknown'),
                    'version': info.get('version', 'Unknown')
                })
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erreur découverte: {e}")
                
        discover_socket.close()
        return clients

class MonitoringServer:
    def __init__(self, port):
        self.port = port
        self.running = False
        
    def start(self):
        """Démarre le serveur de monitoring"""
        self.running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', self.port))
        self.server.listen(5)
        
        # Thread pour accepter les connexions
        threading.Thread(target=self._accept_connections, daemon=True).start()
        
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        self.server.close()
        
    def _accept_connections(self):
        """Accepte les connexions des clients"""
        while self.running:
            try:
                client, addr = self.server.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    print(f"Erreur connexion: {e}")
                    
    def _handle_client(self, client, addr):
        """Gère la connexion avec un client"""
        try:
            while self.running:
                # Collecte les informations système
                system_info = {
                    'cpu': {
                        'percent': psutil.cpu_percent(interval=1),
                        'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                        'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    },
                    'memory': psutil.virtual_memory()._asdict(),
                    'swap': psutil.swap_memory()._asdict(),
                    'disks': {
                        part.mountpoint: psutil.disk_usage(part.mountpoint)._asdict()
                        for part in psutil.disk_partitions()
                        if part.fstype
                    },
                    'network': {
                        iface: psutil.net_io_counters(pernic=True)[iface]._asdict()
                        for iface in psutil.net_if_stats().keys()
                    }
                }
                
                # Envoie les informations au client
                client.send(json.dumps(system_info).encode())
                
        except Exception as e:
            print(f"Erreur client {addr}: {e}")
        finally:
            client.close()
