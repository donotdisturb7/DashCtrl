import psutil
import socket
import json
import platform
import time
import sys
import os

def get_system_stats():
    stats = {}
    
    # CPU
    stats['cpu_name'] = platform.processor()
    stats['cpu_total'] = psutil.cpu_percent()
    stats['cpu_info'] = {
        'physical_cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }
    
    # Mémoire
    mem = psutil.virtual_memory()
    stats['memory'] = {
        'total': mem.total,
        'available': mem.available,
        'used': mem.used,
        'cached': mem.cached if hasattr(mem, 'cached') else 0,
        'percent': mem.percent
    }
    
    # Disques
    disk_info = {'partitions': []}
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_info['partitions'].append({
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            })
        except Exception:
            continue
    stats['disk'] = disk_info
    
    return stats

def main():
    
    SERVER_HOST = 'localhost'
    SERVER_PORT = 5000
    
    # Créer une socket client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Se connecter au serveur
        client.connect((SERVER_HOST, SERVER_PORT))
        
        # Envoyer les informations initiales
        info = {
            "hostname": socket.gethostname(),
            "system": platform.system(),
            "version": platform.version()
        }
        client.send(json.dumps(info).encode())
        
     
        while True:
            try:
                # Recevoir la commande du serveur
                data = client.recv(1024).decode()
                if not data:
                    break
                
                command = json.loads(data)
                
                if command["command"] == "get_stats":
                    # Obtenir et envoyer les statistiques système
                    stats = get_system_stats()
                    client.send(json.dumps(stats).encode())
                
                elif command["command"] == "shutdown":
                    # Éteindre l'ordinateur
                    if platform.system() == "Windows":
                        os.system("shutdown /s /t 1")
                    else:
                        os.system("shutdown -h now")
                    break
            
            except Exception as e:
                print(f"Erreur lors du traitement de la commande: {e}")
                break
    
    except Exception as e:
        print(f"Erreur de connexion: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    main()
