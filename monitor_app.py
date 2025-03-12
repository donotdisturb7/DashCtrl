import customtkinter as ctk
import json
import socket
import threading
from datetime import datetime
import tkinter as tk
from typing import Dict, Optional
import humanize

class MonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("DashCtrl")
        self.geometry("800x600")
        
        # Configuration de la disposition de la grille
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Initialisation des variables
        self.current_page = None
        self.connected_computers: Dict[str, dict] = {}
        self.selected_computer: Optional[str] = None
        
        # Création du cadre de navigation
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)
        
        # Étiquette du nom de l'application
        self.app_name = ctk.CTkLabel(self.navigation_frame, text="DashCtrl",
                                   font=ctk.CTkFont(size=20, weight="bold"))
        self.app_name.grid(row=0, column=0, padx=20, pady=20)
        
        # Boutons de navigation
        self.home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                       text="Accueil", command=self.show_welcome_page)
        self.home_button.grid(row=1, column=0, sticky="ew")
        
        self.computers_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                            text="Ordinateurs en ligne", command=self.show_computers_page)
        self.computers_button.grid(row=2, column=0, sticky="ew")
        
        # Bouton "À propos"
        self.about_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                            text="À propos", command=self.show_about_page)
        self.about_button.grid(row=3, column=0, sticky="ew")
        
        # Création du cadre principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Afficher la page d'accueil par défaut
        self.show_welcome_page()
        
        # Démarrer le thread du serveur
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
    
    def show_welcome_page(self):
        if self.current_page:
            self.current_page.destroy()
        
        self.welcome_frame = ctk.CTkFrame(self.main_frame)
        self.welcome_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        title = ctk.CTkLabel(self.welcome_frame, 
                           text="Bienvenue sur DashCtrl",
                           font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        description = ctk.CTkLabel(self.welcome_frame,
                                 text="Surveillez vos ordinateurs facilement",
                                 font=ctk.CTkFont(size=14))
        description.pack(pady=20)
        
        self.current_page = self.welcome_frame
    
    def show_computers_page(self):
        if self.current_page:
            self.current_page.destroy()
        
        self.computers_frame = ctk.CTkFrame(self.main_frame)
        self.computers_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Titre
        title = ctk.CTkLabel(self.computers_frame,
                           text="Ordinateurs Connectés",
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        # Liste des ordinateurs
        self.computers_list = ctk.CTkScrollableFrame(self.computers_frame)
        self.computers_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_computers_list()
        self.current_page = self.computers_frame
    
    def show_about_page(self):
        if self.current_page:
            self.current_page.destroy()

        self.about_frame = ctk.CTkFrame(self.main_frame)
        self.about_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        title_label = ctk.CTkLabel(self.about_frame, text="À propos de DashCtrl", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20)

        description_label = ctk.CTkLabel(self.about_frame, text="Ce projet a été réalisé par:", font=ctk.CTkFont(size=16))
        description_label.pack(pady=10)

        developers_text = "Développeurs:\nRénald DESIRE\nJean-Michel Harrow"  
        developers_label = ctk.CTkLabel(self.about_frame, text=developers_text, justify="left")
        developers_label.pack(pady=10)

        self.current_page = self.about_frame
    
    def show_stats_page(self, computer_id: str):
        if self.current_page:
            self.current_page.destroy()
        
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # En-tête
        header_frame = ctk.CTkFrame(self.stats_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        back_button = ctk.CTkButton(header_frame, text="← Retour",
                                  command=self.show_computers_page,
                                  width=100)
        back_button.pack(side="left")
        
        computer_name = self.connected_computers[computer_id]["hostname"]
        title = ctk.CTkLabel(header_frame,
                           text=f"Statistiques: {computer_name}",
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(side="left", padx=20)
        
        shutdown_button = ctk.CTkButton(header_frame, 
                                      text="Éteindre",
                                      command=lambda: self.shutdown_computer(computer_id),
                                      fg_color="red",
                                      width=100)
        shutdown_button.pack(side="right")
        
        # Contenu
        content = ctk.CTkScrollableFrame(self.stats_frame)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # CPU Frame
        cpu_frame = ctk.CTkFrame(content)
        cpu_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(cpu_frame, text="CPU", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.cpu_info = ctk.CTkLabel(cpu_frame, text="")
        self.cpu_info.pack(pady=5)
        
        # Mémoire Frame
        mem_frame = ctk.CTkFrame(content)
        mem_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(mem_frame, text="Mémoire", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.mem_info = ctk.CTkLabel(mem_frame, text="")
        self.mem_info.pack(pady=5)
        
        # Disque Frame
        disk_frame = ctk.CTkFrame(content)
        disk_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(disk_frame, text="Disques", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.disk_table = ctk.CTkTextbox(disk_frame, height=150)
        self.disk_table.pack(fill="x", padx=5, pady=5)
        
        self.current_page = self.stats_frame
        self.selected_computer = computer_id
        
        # Commencer la mise à jour des statistiques
        self.update_stats()
    
    def update_computers_list(self):
        # Effacer les éléments existants
        for widget in self.computers_list.winfo_children():
            widget.destroy()
        
        # Ajouter les ordinateurs connectés
        for computer_id, info in self.connected_computers.items():
            computer_frame = ctk.CTkFrame(self.computers_list)
            computer_frame.pack(fill="x", padx=10, pady=5)
            
            name_label = ctk.CTkLabel(computer_frame,
                                    text=f"Ordinateur: {info['hostname']}",
                                    font=ctk.CTkFont(weight="bold"))
            name_label.pack(side="left", padx=10, pady=10)
            
            status_label = ctk.CTkLabel(computer_frame,
                                      text="En ligne",
                                      text_color="green")
            status_label.pack(side="left", padx=10)
            
            view_button = ctk.CTkButton(computer_frame,
                                      text="Voir Stats",
                                      command=lambda cid=computer_id: self.show_stats_page(cid))
            view_button.pack(side="right", padx=10)
    
    def update_stats(self):
        if not self.selected_computer or self.selected_computer not in self.connected_computers:
            return
            
        try:
            client_socket = self.connected_computers[self.selected_computer]["socket"]
            client_socket.send(json.dumps({"command": "get_stats"}).encode())
            
            response = client_socket.recv(4096).decode()
            stats = json.loads(response)
            
            # Mise à jour CPU
            cpu_text = (
                f"Modèle: {stats['cpu_name']}\n"
                f"Utilisation totale: {stats['cpu_total']}%\n"
                f"Cœurs physiques: {stats['cpu_info']['physical_cores']}\n"
                f"Threads: {stats['cpu_info']['threads']}\n"
                f"Fréquence: {stats['cpu_info']['freq_current']:.0f} MHz"
            )
            self.cpu_info.configure(text=cpu_text)
            
            # Mise à jour Mémoire
            mem = stats['memory']
            mem_text = (
                f"Total: {humanize.naturalsize(mem['total'])}\n"
                f"Utilisé: {humanize.naturalsize(mem['used'])} ({mem['percent']}%)\n"
                f"Disponible: {humanize.naturalsize(mem['available'])}\n"
                f"Cache: {humanize.naturalsize(mem['cached'])}"
            )
            self.mem_info.configure(text=mem_text)
            
            # Mise à jour Disques
            self.disk_table.delete('1.0', tk.END)
            disk_text = f"{'Partition':<15} {'Type':<10} {'Total':<10} {'Utilisé':<10} {'Libre':<10} {'%':<5}\n"
            disk_text += "-" * 60 + "\n"
            
            for partition in stats['disk']['partitions']:
                disk_text += f"{partition['device']:<15} {partition['fstype']:<10} "
                disk_text += f"{humanize.naturalsize(partition['total']):>10} "
                disk_text += f"{humanize.naturalsize(partition['used']):>10} "
                disk_text += f"{humanize.naturalsize(partition['free']):>10} "
                disk_text += f"{partition['percent']:>3}%\n"
            
            self.disk_table.insert('1.0', disk_text)
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour des statistiques: {e}")
        
        if self.current_page == self.stats_frame:
            self.after(1000, self.update_stats)
    
    def shutdown_computer(self, computer_id):
        if not computer_id in self.connected_computers:
            return
        
        if not ctk.CTkMessagebox(title="Confirmation",
                               message="Voulez-vous vraiment éteindre cet ordinateur ?",
                               icon="warning",
                               option_1="Oui",
                               option_2="Non").get() == "Oui":
            return
        
        try:
            client_socket = self.connected_computers[computer_id]["socket"]
            client_socket.send(json.dumps({"command": "shutdown"}).encode())
        except Exception as e:
            print(f"Erreur lors de l'extinction: {e}")
    
    def run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 5000))
        server.listen(5)
        
        while True:
            try:
                client, addr = server.accept()
                
                # Recevoir les informations initiales du client
                data = client.recv(1024).decode()
                info = json.loads(data)
                
                # Générer un ID unique pour cet ordinateur
                computer_id = f"{addr[0]}:{addr[1]}"
                
                # Stocker les informations du client
                self.connected_computers[computer_id] = {
                    "socket": client,
                    "address": addr,
                    "hostname": info["hostname"],
                    "system": info["system"],
                    "version": info["version"]
                }
                
                # Mettre à jour l'interface
                self.after(0, self.update_computers_list)
                
            except Exception as e:
                print(f"Erreur de connexion: {e}")

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
