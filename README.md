# DashCtrl - Moniteur Système

DashCtrl est une application client-serveur de surveillance système écrite en Python. Elle permet de surveiller en temps réel les ressources système (CPU, mémoire, disques) de plusieurs ordinateurs à distance.

## Architecture

L'application est composée de deux parties :

### 1. Client (`client.py`)

Le client est le programme qui s'exécute sur les machines à surveiller. Il collecte les informations système et les envoie au serveur.

#### Fonctionnalités principales :

- **Collecte des statistiques système** (`get_system_stats()`)
  ```python
  def get_system_stats():
      stats = {}
      # CPU
      stats['cpu_name'] = platform.processor()
      stats['cpu_total'] = psutil.cpu_percent()
      stats['cpu_info'] = {
          'physical_cores': psutil.cpu_count(logical=False),
          'threads': psutil.cpu_count(logical=True),
          'freq_current': psutil.cpu_freq().current
      }
      # ...
  ```
  - Utilise `psutil` pour collecter :
    - Informations CPU (utilisation, nombre de cœurs, fréquence)
    - État de la mémoire (total, utilisé, disponible, cache)
    - Informations sur les disques (partitions, espace utilisé/libre)

- **Connexion au serveur** (`main()`)
  - Se connecte au serveur sur localhost:5000
  - Envoie les informations d'identification initiales
  - Attend et traite les commandes du serveur

- **Commandes supportées**
  - `get_stats` : Renvoie les statistiques système
  - `shutdown` : Éteint l'ordinateur (Windows ou Linux)

### 2. Serveur (`monitor_app.py`)

Le serveur est l'interface graphique qui affiche les informations des clients connectés.

#### Interface utilisateur :

1. **Page d'accueil**
   - Message de bienvenue
   - Description simple de l'application

2. **Liste des ordinateurs**
   - Affiche tous les ordinateurs connectés
   - Pour chaque ordinateur :
     - Nom d'hôte
     - Statut de connexion
     - Bouton pour voir les statistiques
     - Bouton pour éteindre

3. **Page des statistiques**
   - **En-tête**
     - Bouton retour
     - Nom de l'ordinateur
     - Bouton d'extinction
   
   - **Informations CPU**
     ```python
     cpu_text = (
         f"Modèle: {stats['cpu_name']}\n"
         f"Utilisation totale: {stats['cpu_total']}%\n"
         f"Cœurs physiques: {stats['cpu_info']['physical_cores']}\n"
         f"Threads: {stats['cpu_info']['threads']}\n"
         f"Fréquence: {stats['cpu_info']['freq_current']:.0f} MHz"
     )
     ```
   
   - **Informations Mémoire**
     - Utilise `humanize` pour formater les tailles
     - Affiche : Total, Utilisé, Disponible, Cache
   
   - **Tableau des Disques**
     - Liste des partitions avec :
       - Nom du périphérique
       - Type de système de fichiers
       - Espace total/utilisé/libre
       - Pourcentage d'utilisation

#### Fonctionnalités techniques :

1. **Gestion des connexions**
   - Écoute sur le port 5000
   - Accepte les connexions entrantes
   - Maintient une liste des clients connectés

2. **Mise à jour en temps réel**
   - Interroge les clients toutes les secondes
   - Met à jour l'interface utilisateur
   - Gère les déconnexions

3. **Interface graphique**
   - Utilise `customtkinter` pour une interface moderne
   - Organisation en onglets et frames
   - Mise en page responsive

## Dépendances

- `psutil` : Collecte des statistiques système
- `customtkinter` : Interface graphique moderne
- `humanize` : Formatage des tailles en unités lisibles
- Bibliothèques standard Python :
  - `socket` : Communication réseau
  - `json` : Sérialisation des données
  - `threading` : Gestion des connexions multiples

## Installation

1. Installer les dépendances :
   ```bash
   pip install psutil customtkinter humanize
   ```

2. Lancer le serveur sur la machine principale :
   ```bash
   python monitor_app.py
   ```

3. Lancer le client sur chaque machine à surveiller :
   ```bash
   python client.py
   ```

## Sécurité

- Les connexions sont en local par défaut (localhost)
- La commande d'extinction nécessite les permissions appropriées
