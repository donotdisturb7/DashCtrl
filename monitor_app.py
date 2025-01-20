import customtkinter as ctk
import json
import socket
import threading
from datetime import datetime
import tkinter as tk
from typing import Dict, Optional
from PIL import Image

class MonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("DashCtrl")
        self.geometry("1000x600")
        
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
        
        # Création du cadre principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Initialisation des pages
        self.welcome_frame = None
        self.computers_frame = None
        self.stats_frame = None
        
        # Afficher la page d'accueil par défaut
        self.show_welcome_page()
        
        # Démarrer le thread du serveur
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
    
    def show_welcome_page(self):
        if self.current_page:
            self.current_page.grid_forget()
        
        if not self.welcome_frame:
            self.welcome_frame = ctk.CTkFrame(self.main_frame)
            self.welcome_frame.grid_rowconfigure(0, weight=1)
            self.welcome_frame.grid_columnconfigure(0, weight=1)
            
            welcome_content = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
            welcome_content.grid(row=0, column=0, padx=20, pady=20)
            
            title = ctk.CTkLabel(welcome_content, 
                               text="Bienvenue sur DashCtrl",
                               font=ctk.CTkFont(size=24, weight="bold"))
            title.pack(pady=20)
            
            description = ctk.CTkLabel(welcome_content,
                                     text="Surveillez vos ordinateurs facilement.\n\n" +
                                     "• Visualisez tous les ordinateurs connectés\n" +
                                     "• Surveillez les statistiques système en temps réel\n" +
                                     "• Interface simple et intuitive",
                                     font=ctk.CTkFont(size=14))
            description.pack(pady=20)
        
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        self.current_page = self.welcome_frame
        
    def show_computers_page(self):
        if self.current_page:
            self.current_page.grid_forget()
            
        if not self.computers_frame:
            self.computers_frame = ctk.CTkFrame(self.main_frame)
            self.computers_frame.grid_rowconfigure(1, weight=1)
            self.computers_frame.grid_columnconfigure(0, weight=1)
            
            # Titre
            title = ctk.CTkLabel(self.computers_frame,
                               text="Ordinateurs Connectés",
                               font=ctk.CTkFont(size=20, weight="bold"))
            title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
            
            # Liste des ordinateurs
            self.computers_list = ctk.CTkScrollableFrame(self.computers_frame)
            self.computers_list.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
            
        self.update_computers_list()
        self.computers_frame.grid(row=0, column=0, sticky="nsew")
        self.current_page = self.computers_frame
    
    def show_stats_page(self, computer_id: str):
        if self.current_page:
            self.current_page.grid_forget()
            
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.grid_rowconfigure(1, weight=1)
        self.stats_frame.grid_columnconfigure(0, weight=1)
        
        # En-tête avec bouton retour
        header_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        back_button = ctk.CTkButton(header_frame, text="← Retour",
                                  command=self.show_computers_page,
                                  width=100)
        back_button.pack(side="left")
        
        computer_name = self.connected_computers[computer_id]["hostname"]
        title = ctk.CTkLabel(header_frame,
                           text=f"Statistiques pour {computer_name}",
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(side="left", padx=20)
        
        # Contenu des statistiques
        stats_content = ctk.CTkFrame(self.stats_frame)
        stats_content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Création des étiquettes pour différentes statistiques
        self.cpu_label = ctk.CTkLabel(stats_content, text="Utilisation CPU: ---%")
        self.cpu_label.pack(pady=10)
        
        self.memory_label = ctk.CTkLabel(stats_content, text="Utilisation Mémoire: ---%")
        self.memory_label.pack(pady=10)
        
        self.disk_label = ctk.CTkLabel(stats_content, text="Utilisation Disque: ---%")
        self.disk_label.pack(pady=10)
        
        self.stats_frame.grid(row=0, column=0, sticky="nsew")
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
            
        # Demander la mise à jour des statistiques au client
        try:
            client_socket = self.connected_computers[self.selected_computer]["socket"]
            client_socket.send(json.dumps({"command": "get_stats"}).encode())
            
            response = client_socket.recv(1024).decode()
            stats = json.loads(response)
            
            self.cpu_label.configure(text=f"Utilisation CPU: {stats['cpu_percent']}%")
            self.memory_label.configure(text=f"Utilisation Mémoire: {stats['memory_percent']}%")
            self.disk_label.configure(text=f"Utilisation Disque: {stats['disk_percent']}%")
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour des statistiques: {e}")
        
        if self.current_page == self.stats_frame:
            self.after(1000, self.update_stats)
    
    def run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 5000))
        server.listen(5)
        
        while True:
            client_socket, address = server.accept()
            client_thread = threading.Thread(target=self.handle_client,
                                          args=(client_socket, address),
                                          daemon=True)
            client_thread.start()
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        try:
            # Obtenir les informations initiales de l'ordinateur
            info = client_socket.recv(1024).decode()
            computer_info = json.loads(info)
            computer_id = f"{address[0]}:{address[1]}"
            
            self.connected_computers[computer_id] = {
                "socket": client_socket,
                "address": address,
                "hostname": computer_info["hostname"]
            }
            
            # Mettre à jour l'interface
            self.after(0, self.update_computers_list)
            
            # Maintenir la connexion active et gérer la déconnexion
            while True:
                try:
                    # Simple ping pour vérifier si le client est toujours connecté
                    client_socket.send(json.dumps({"command": "ping"}).encode())
                    client_socket.recv(1024)
                    
                except Exception:
                    break
                    
        except Exception as e:
            print(f"Erreur lors de la gestion du client: {e}")
        finally:
            # Nettoyer lors de la déconnexion
            if computer_id in self.connected_computers:
                del self.connected_computers[computer_id]
                self.after(0, self.update_computers_list)
            client_socket.close()

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
