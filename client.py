import socket
import json
import psutil
import platform
import time
import threading

class MonitoringClient:
    def __init__(self, server_host='localhost', server_port=5000):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            
            # Envoyer les informations initiales de l'ordinateur
            initial_info = {
                "hostname": platform.node(),
                "system": platform.system(),
                "version": platform.version()
            }
            self.socket.send(json.dumps(initial_info).encode())
            
            # Commencer à écouter les commandes
            self.listen_for_commands()
            
        except Exception as e:
            print(f"Échec de la connexion: {e}")
            self.connected = False
    
    def get_system_stats(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    
    def handle_command(self, command_data):
        command = command_data.get("command")
        
        if command == "get_stats":
            stats = self.get_system_stats()
            return json.dumps(stats)
        elif command == "ping":
            return json.dumps({"status": "alive"})
        
        return json.dumps({"error": "Commande inconnue"})
    
    def listen_for_commands(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                
                command_data = json.loads(data)
                response = self.handle_command(command_data)
                self.socket.send(response.encode())
                
            except Exception as e:
                print(f"Erreur pendant l'écoute: {e}")
                break
        
        self.connected = False
        if self.socket:
            self.socket.close()
    
    def run(self):
        while True:
            if not self.connected:
                print("Tentative de connexion au serveur...")
                self.connect()
            time.sleep(5)  # Attendre avant de réessayer si la connexion échoue

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Client de Surveillance Système')
    parser.add_argument('--host', default='localhost',
                      help='Adresse du serveur hôte (défaut: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Port du serveur (défaut: 5000)')
    
    args = parser.parse_args()
    
    client = MonitoringClient(args.host, args.port)
    client.run()
