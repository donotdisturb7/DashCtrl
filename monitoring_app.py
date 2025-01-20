import sys
import os
import psutil
import socket
import json
import threading
import time
from datetime import datetime
import time
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                           QListWidget, QListWidgetItem)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QIcon
import pyqtgraph as pg
from network_discovery import NetworkDiscovery

class IntroWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("DashCtrl")
        title.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Application de surveillance système permettant de monitorer\n"
            "les ressources de plusieurs ordinateurs sur votre réseau.\n\n"
            "• Surveillance CPU en temps réel\n"
            "• Utilisation mémoire et disque\n"
            "• Trafic réseau\n"
            "• Multi-machines"
        )
        description.setFont(QFont('Arial', 12))
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        # Bouton Continuer
        continue_btn = QPushButton("Continuer")
        continue_btn.setFixedSize(200, 50)
        continue_btn.clicked.connect(self.on_continue)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(continue_btn)
        btn_layout.addStretch()
        
        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def on_continue(self):
        self.parent().setCurrentIndex(1)  # Change to computer list window

class ComputerListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.network = NetworkDiscovery()
        
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Ordinateurs Disponibles")
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Liste des ordinateurs
        self.computer_list = QListWidget()
        self.computer_list.itemDoubleClicked.connect(self.on_computer_selected)
        layout.addWidget(self.computer_list)
        
        # Boutons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.clicked.connect(self.refresh_computers)
        
        back_btn = QPushButton("Retour")
        back_btn.clicked.connect(lambda: self.parent().setCurrentIndex(0))
        
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def refresh_computers(self):
        """Rafraîchit la liste des ordinateurs disponibles"""
        self.computer_list.clear()
        computers = self.network.discover_clients()
        
        for computer in computers:
            item = QListWidgetItem(
                f"{computer['hostname']} ({computer['address']})\n"
                f"OS: {computer['os']} - {computer['version']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, computer)
            self.computer_list.addItem(item)
            
    def on_computer_selected(self, item):
        """Gère la sélection d'un ordinateur"""
        computer = item.data(Qt.ItemDataRole.UserRole)
        monitoring_window = self.parent().widget(2)  # Get monitoring window
        monitoring_window.connect_to_computer(computer)
        self.parent().setCurrentIndex(2)  # Switch to monitoring window

class MonitoringWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # En-tête
        header_layout = QHBoxLayout()
        
        self.computer_label = QLabel()
        self.computer_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        header_layout.addWidget(self.computer_label)
        
        back_btn = QPushButton("Retour à la liste")
        back_btn.clicked.connect(self.on_back)
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)
        
        # Graphiques
        self.cpu_plot = self.create_plot("CPU Usage (%)")
        self.memory_plot = self.create_plot("Memory Usage (%)")
        self.disk_plot = self.create_plot("Disk Usage (%)")
        self.network_plot = self.create_plot("Network Usage (KB/s)")
        
        # Layout des graphiques
        plots_layout = QHBoxLayout()
        plots_layout.addWidget(self.cpu_plot)
        plots_layout.addWidget(self.memory_plot)
        
        plots_layout2 = QHBoxLayout()
        plots_layout2.addWidget(self.disk_plot)
        plots_layout2.addWidget(self.network_plot)
        
        layout.addLayout(plots_layout)
        layout.addLayout(plots_layout2)
        
        self.setLayout(layout)
        
        # Données
        self.reset_data()
        
        # Socket client
        self.client_socket = None
        self.is_connected = False
        
    def reset_data(self):
        """Réinitialise les données des graphiques"""
        self.cpu_data = []
        self.memory_data = []
        self.disk_data = []
        self.network_sent_data = []
        self.network_recv_data = []
        self.timestamps = []
        
    def create_plot(self, title):
        """Crée un widget de graphique"""
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('w')
        plot_widget.setTitle(title)
        plot_widget.showGrid(x=True, y=True)
        return plot_widget
        
    def connect_to_computer(self, computer):
        """Se connecte à l'ordinateur sélectionné"""
        self.computer_label.setText(f"Monitoring: {computer['hostname']}")
        
        # Réinitialise les données
        self.reset_data()
        
        # Ferme la connexion existante si présente
        if self.client_socket:
            self.is_connected = False
            self.client_socket.close()
            
        # Nouvelle connexion
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((computer['address'], computer['port']))
            self.is_connected = True
            
            # Démarre le thread de réception
            threading.Thread(target=self._receive_data, daemon=True).start()
            
        except Exception as e:
            print(f"Erreur connexion: {e}")
            
    def _receive_data(self):
        """Reçoit les données du serveur"""
        while self.is_connected and self.client_socket:
            try:
                data = self.client_socket.recv(1024 * 1024)
                if not data:
                    break
                    
                system_info = json.loads(data.decode())
                self.update_plots(system_info)
                
            except Exception as e:
                print(f"Erreur réception: {e}")
                break
                
        self.is_connected = False
        
    def update_plots(self, data):
        """Met à jour les graphiques"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.timestamps.append(timestamp)
        if len(self.timestamps) > 60:
            self.timestamps.pop(0)
            
        # CPU
        cpu_avg = data['cpu']['percent']
        self.cpu_data.append(cpu_avg)
        if len(self.cpu_data) > 60:
            self.cpu_data.pop(0)
        self.cpu_plot.clear()
        self.cpu_plot.plot(self.cpu_data, pen='b')
        
        # Mémoire
        memory_percent = data['memory']['percent']
        self.memory_data.append(memory_percent)
        if len(self.memory_data) > 60:
            self.memory_data.pop(0)
        self.memory_plot.clear()
        self.memory_plot.plot(self.memory_data, pen='r')
        
        # Disque (utilise le premier disque trouvé)
        if data['disks']:
            first_disk = next(iter(data['disks'].values()))
            self.disk_data.append(first_disk['percent'])
            if len(self.disk_data) > 60:
                self.disk_data.pop(0)
            self.disk_plot.clear()
            self.disk_plot.plot(self.disk_data, pen='g')
            
        # Réseau (utilise la première interface trouvée)
        if data['network']:
            first_net = next(iter(data['network'].values()))
            bytes_sent = first_net['bytes_sent'] / 1024  # KB
            bytes_recv = first_net['bytes_recv'] / 1024  # KB
            
            self.network_sent_data.append(bytes_sent)
            self.network_recv_data.append(bytes_recv)
            
            if len(self.network_sent_data) > 60:
                self.network_sent_data.pop(0)
                self.network_recv_data.pop(0)
                
            self.network_plot.clear()
            self.network_plot.plot(self.network_sent_data, pen='y', name='Sent')
            self.network_plot.plot(self.network_recv_data, pen='m', name='Received')
            
    def on_back(self):
        """Retourne à la liste des ordinateurs"""
        if self.client_socket:
            self.is_connected = False
            self.client_socket.close()
        self.parent().setCurrentIndex(1)
        
    def closeEvent(self, event):
        """Gère la fermeture de la fenêtre"""
        if self.client_socket:
            self.is_connected = False
            self.client_socket.close()
        event.accept()

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DashCtrl')
        self.setGeometry(100, 100, 1200, 800)
        
        # Création du widget empilé pour gérer les différentes fenêtres
        self.stacked_widget = QStackedWidget()
        
        # Ajout des fenêtres
        self.stacked_widget.addWidget(IntroWindow())
        self.stacked_widget.addWidget(ComputerListWindow())
        self.stacked_widget.addWidget(MonitoringWindow())
        
        self.setCentralWidget(self.stacked_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())
