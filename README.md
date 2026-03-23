# Projet SMA - Collecte et Tri de Déchets Radioactifs

**Date de création :** 16/03/2026  
**Membres du groupe (Groupe 6) :** 
- Nicolas Charronnière
- Paul Guimbert


## Description du Projet
Ce projet implémente un Système Multi-Agents (SMA) développé en Python avec la bibliothèque **Mesa**. 
Il simule un environnement divisé en trois zones de radioactivité croissante où des robots spécialisés doivent coopérer indirectement pour nettoyer l'espace. Les robots ramassent des déchets, les fusionnent pour les transformer, et les font transiter de zone en zone jusqu'à leur évacuation finale.


## Prérequis et Installation

Assurez-vous d'avoir Python installé sur votre machine. Utiliser le fichier `requirements.txt` pour installer l'ensemble des libraires nécessaires au bon fonctionnement du projet.

```bash
pip install -r requirements.txt
```

## Instructions d'exécution

Le projet utilise **Solara** pour le rendu de l'interface visuelle et du dashboard. Pour lancer le serveur web contenant la simulation :

```bash
solara run server.py
```
Une fois la commande lancée, un lien local (généralement `http://localhost:8765`) s'affichera dans votre terminal. Ouvrez ce lien dans votre navigateur web pour interagir avec la simulation.

##  Choix Conceptuels et Architecture

### 1. L'Environnement
L'espace est une grille bidimensionnelle non torique (`MultiGrid`) divisée verticalement en trois zones :
- **Zone 1 (Verte)** : Faible radioactivité.
- **Zone 2 (Jaune)** : Radioactivité moyenne.
- **Zone 3 (Rouge)** : Forte radioactivité, comportant une zone d'évacuation définitive (`WasteDisposalZone`).

### 2. Les Agents
Nous avons implémenté trois types de robots, chacun assigné à un niveau de déchet spécifique :
- **GreenAgent** : Ramasse les déchets verts, en assemble 2 pour créer un déchet jaune, et le dépose à la frontière de la Zone 2.
- **YellowAgent** : Ramasse les déchets jaunes, en assemble 2 pour créer un déchet rouge, et le dépose à la frontière de la Zone 3.
- **RedAgent** : Ramasse les déchets rouges et les achemine jusqu'aux `WasteDisposalZone` situées tout à droite de la grille.

### 3. Architecture Interne des Robots
Les robots suivent un cycle d'action strict basé sur la séparation entre la perception, la base de connaissances et la délibération :
1. **Perception (`get_percepts`)** : L'environnement renvoie les données de la case actuelle et des cases adjacentes au robot.
2. **Mise à jour (`update`)** : Le robot met à jour sa base de connaissances stricte (`self.knowledge`) avec les nouvelles perceptions sans manipuler directement le modèle.
3. **Délibération (`deliberate`)** : Basé sur sa base de connaissances, le robot choisit une action parmi : `move`, `pick`, `put`, ou `transform`. 
Pour l'instant ce choix ce fait de manière semi-aléatoire selon ce principe pour les robots verts et jaune:
- Si un agent possède deux déchets de sont types, il `transform`
- Sinon, s'il possède un déchets de type supérieur à lui et que la case à sa droite est de niveau supérieur, il `put`
- Sinon, s'il , s'il possède un déchets de type supérieur à lui, il `move` il move vers la droite.
- Sinon, s'il est sur un déchet de son niveau, il `pick`.
- Sinon, il `move` dans une des qatres directions de manière aléatoire (uniformement).
Pour le robot rouge, la plupart des règles sont similaires:
- Si l'agent possède un déchet rouge et qu'il est sur la zone de dépot de déchets, il `put`.
- Si l'agent possède un déchet rouge et qu'il n'est pas sur l'extremité droite de la grille, il `move `vers la droite
- Si l'agent possède un déchet rouge et qu'il est l'extremité droite de la grille, il `move ` aléatoirement vers le haut ou le bas (uniforme).
- Sinon, s'il est sur un déchet rouge, il `pick`.
- Sinon, il `move` dans une des quatres directions de manière aléatoire (uniformement).
En checkant bien dans cet ordre les actions possibles, cela globalement de demander des actions impossibles tel que récupérer trop de déchets en même temps. Cela converge bien vers le ramassage de tout les déchets.

4. **Action (`do`)** : L'environnement résout l'action demandée par l'agent si elle est possible, applique les conséquences physiques (ex: retrait d'un objet de la grille) et renvoie les nouvelles perceptions.


## État d'avancement et Résultats

**Fonctionnalités achevées :**
- Génération procédurale de la carte et répartition des zones.
- Modèle de délibération autonome des agents opérationnel, avec un déplacement random tant que l'agent peut encore ramasser et vers la zone de dépot lorsqu'il ne peut plus.
- Mécanique de ramassage, transformation de l'inventaire et dépôt.
- Collecte de données en temps réel (`DataCollector`) et affichage d'un graphique dynamique suivant la quantité de déchets restants pour chaque couleur.
- Interface visuelle interactive avec `Solara` et `Mesa`:
  - Sliders pour choisir la taille de chaque zone, le noombre de déchets de chaque type et le nombre de robots de chaque type.
  - Grille représentant l'environnement
  - Courbes d'évolution des quantitées de chaque type de déchets.
- Critère d'arrêt d'évolution lorsque l'ensemble des déchets sont soit bloqués dans un inventaire (pour l'instant pas de drop d'un waste de même type que le robot), soit détruits.

**Résultats observés :**
Grâce au dashboard dynamique, on observe bien la courbe de déchets verts et jaunes diminuer au profit de déchets de niveaux supérieurs, jusqu'à l'évacuation complète par les agents rouges. L'architecture développée prévient les erreurs de collisions ou de triche : un agent ne se déplace ou ne ramasse un objet que si l'environnement valide la faisabilité de son intention.

Certains déchets vert et jaune ne disparaissent pas dans certains cas, car ils sont bloqués dans les inventaires des robots sans pouvoir être transformés car plus aucun déchet du même type n'est au sol.
Pour gérer ce problème, il faudrait rajouter une petite chance de `put` l'objet transporté au lieu de se déplacer lorsqu'un agent possède un seul objet de son type. Il faudrait alors adapter la condition de fin d'épisode également


**Pistes à explorer :**
- *Stratégie naive:* Stratégie purement aléatoire, à part le fait que lorsqu'un robot est sur un waste qu'il peut récupérer il le récupère, lorsqu'un robot vert ou jaune a transformé un waste au niveau supérieur il va jusqu'à la frontière et le drop, et lorsqu'un rouge récupère 
- *Stratégie sans comm:* Regarde les knowledge passés et trouve le waste le plus proche et va le chercher.
- *Stratégie communication 1 à 1:* Quand deux agents du même type ont un waste, ils se retrouvent pour se passer le waste et transform
- *Stratégie communication ultime:* Les agents sont au courant de tout ce que les autres agent savent et optimisent le fait de se retrouver pour transform ou d'aller chercher les wastes les plus proches.