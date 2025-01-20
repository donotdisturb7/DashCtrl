import psutil
import socket
import json
import platform
import time
import sys
import os
import subprocess

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

def try_shutdown_linux():
    """Essaie différentes méthodes d'extinction sur Linux"""
    commands = [
        # D'abord essayer systemctl qui est moderne et largement supporté
        ["systemctl", "poweroff"],
        # Commandes shutdown classiques
        ["shutdown", "-h", "now"],
        ["shutdown", "-P", "now"],
        # Commande poweroff directe
        ["poweroff"],
        # dbus-send pour les systèmes utilisant D-Bus
        ["dbus-send", "--system", "--print-reply", "--dest=org.freedesktop.login1", 
         "/org/freedesktop/login1", "org.freedesktop.login1.Manager.PowerOff", "boolean:true"]
    ]
    
    for cmd in commands:
        try:
            # Essayer d'abord sans sudo
            if subprocess.run(cmd, stderr=subprocess.DEVNULL).returncode == 0:
                return True
            
            # Si ça ne marche pas, essayer avec sudo
            sudo_cmd = ["sudo", "-n"] + cmd  # -n pour ne pas demander de mot de passe
            if subprocess.run(sudo_cmd, stderr=subprocess.DEVNULL).returncode == 0:
                return True
        except Exception:
            continue
    
    return False

def main():
    # Configuration
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
        
        # Boucle principale
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
                        # Essayer d'éteindre avec différentes méthodes sur Linux
                        if not try_shutdown_linux():
                            print("Impossible d'éteindre le système. Vérifiez les permissions.")
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
