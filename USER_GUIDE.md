
# Guide Utilisateur - Conception d'Arcades Dentaires

Ce guide explique comment utiliser l'application de conception d'arcades dentaires.

## Table des Matières

1. [Premiers Pas](#premiers-pas)
2. [Interface Principale](#interface-principale)
3. [Conception d'Arcade Supérieure](#conception-darcade-supérieure)
4. [Conception d'Arcade Inférieure](#conception-darcade-inférieure)
5. [Gestion des Selles](#gestion-des-selles)
6. [Gestion des Dents](#gestion-des-dents)
7. [Fonctions Avancées](#fonctions-avancées)
8. [Exportation](#exportation)
9. [Raccourcis Clavier](#raccourcis-clavier)

## Premiers Pas

### Lancement de l'Application

1. Assurez-vous que Python 3.8 ou une version supérieure est installé
2. Installez les dépendances requises :
   ```
   pip install -r src/requirements.txt
   ```
3. Lancez l'application :
   ```
   python src/main.py
   ```

### Écran d'Accueil

Lors du premier lancement, vous verrez l'écran d'accueil avec deux options :

- **Arcade Supérieure** : Pour concevoir des arcades dentaires supérieures
- **Arcade Inférieure** : Pour concevoir des arcades dentaires inférieures

Cliquez sur l'une de ces options pour lancer le mode de conception correspondant.

## Interface Principale

Une fois le mode de sélection choisi, l'interface principale s'affiche avec les éléments suivants :

1. **Barre de Menu** : En haut de la fenêtre, avec les options Fichier et Aide
2. **Panneau de Contrôle** : À gauche, avec tous les contrôles de l'application
3. **Canevas** : À droite, où la conception est affichée

## Conception d'Arcade Supérieure

Pour concevoir une arcade supérieure :

1. Sélectionnez "Arcade Supérieure" depuis l'écran d'accueil
2. Le fond d'arcade supérieure s'affiche sur le canevas
3. Utilisez les contrôles pour importer, positionner et modifier des selles

### Éléments Spécifiques à l'Arcade Supérieure

- Les selles disponibles sont situées dans le dossier `data/images/selles/selles_sup`
- Les dents disponibles sont numérotées de 11 à 17 et 21 à 27
- Le fond d'arcade par défaut est `fond_superieur.png`

## Conception d'Arcade Inférieure

Pour concevoir une arcade inférieure :

1. Sélectionnez "Arcade Inférieure" depuis l'écran d'accueil
2. Le fond d'arcade inférieure s'affiche sur le canevas
3. Utilisez les contrôles pour importer, positionner et modifier des selles

### Éléments Spécifiques à l'Arcade Inférieure

- Les selles disponibles sont situées dans le dossier `data/images/selles/selles_inf`
- Les dents disponibles sont numérotées de 31 à 37 et 41 à 47
- Le fond d'arcade par défaut est `fond_inferieur.png`

## Gestion des Selles

### Importer une Selle

1. Dans le panneau de contrôle, cliquez sur "Gestion des Selles"
2. Cliquez sur le bouton "Importer"
3. Sélectionnez une image de selle depuis votre ordinateur
4. La selle sera ajoutée à la liste et sélectionnée automatiquement

### Renommer une Selle

1. Sélectionnez la selle à renommer dans le menu déroulant
2. Cliquez sur "Renommer"
3. Entrez le nouveau nom et cliquez sur OK

### Supprimer une Selle

1. Sélectionnez la selle à supprimer dans le menu déroulant
2. Cliquez sur "Supprimer"
3. Confirmez la suppression

### Effacer Toutes les Selles

1. Dans le panneau de contrôle, cliquez sur "Gestion des Selles"
2. Cliquez sur "Effacer les Selles"
3. Confirmez l'effacement

### Afficher Toutes les Selles

1. Dans le panneau de contrôle, cliquez sur "Gestion des Selles"
2. Cliquez sur "Afficher Toutes les Selles"
3. Toutes les selles enregistrées seront affichées sur le canevas

### Transformer une Selle

Pour transformer une selle (position, rotation, échelle) :

1. Sélectionnez la selle dans le menu déroulant
2. Utilisez les contrôles de transformation pour :
   - Positionner la selle (X, Y)
   - Faire pivoter la selle (Angle)
   - Ajuster l'échelle (Scale)
   - Inverser horizontalement (Flip X)
   - Inverser verticalement (Flip Y)

## Gestion des Dents

### Afficher/Masquer des Dents

1. Dans le panneau de contrôle, cliquez sur "Contrôle des Dents"
2. Pour chaque dent :
   - Cliquez sur le numéro pour afficher/masquer la dent
   - Les dents affichées sont vertes, les dents masquées sont rouges

### Fonctions Globales

1. **Tout Afficher** : Affiche toutes les dents
2. **Tout Masquer** : Masque toutes les dents
3. **Afficher Positions** : Affiche les coordonnées de chaque dent

## Fonctions Avancées

### Enregistrer la Configuration

1. Dans le panneau de contrôle, cliquez sur "Enregistrer Configuration"
2. La configuration actuelle est sauvegardée dans la base de données

### Annuler/Rétablir

- **Ctrl+Z** : Annule la dernière action
- **Ctrl+Y** : Rétablit l'action annulée

### Actualiser

1. Dans le menu Fichier, cliquez sur "Actualiser"
2. L'application recharge tous les éléments depuis la base de données

## Exportation

### Exporter en PNG

1. Dans le panneau de contrôle, cliquez sur "Exporter Arcade PNG"
2. Choisissez l'emplacement et le nom du fichier
3. L'arcade est exportée au format PNG

## Raccourcis Clavier

- **Ctrl+Z** : Annuler
- **Ctrl+Y** : Rétablir
- **Ctrl+S** : Enregistrer
- **F1** : Afficher l'aide

## Dépannage

### Problèmes Courants

1. **L'application ne se lance pas**
   - Vérifiez que Python est installé
   - Vérifiez que toutes les dépendances sont installées

2. **Les images ne s'affichent pas**
   - Vérifiez que les fichiers d'images sont dans les bons dossiers
   - Vérifiez les permissions d'accès aux fichiers

3. **Les données ne se sauvegardent pas**
   - Vérifiez que le dossier `elements_valides` existe et est accessible
   - Vérifiez les permissions d'écriture

### Obtenir de l'Aide

1. Consultez le fichier README.md pour plus d'informations
2. Utilisez le menu Aide > Guide de l'Utilisateur
3. Contactez l'équipe de développement via GitHub

## Mises à Jour

Pour mettre à jour l'application :

1. Téléchargez la dernière version depuis le dépôt GitHub
2. Remplacez les anciens fichiers par les nouveaux
3. Lancez l'application

## Conclusion

Ce guide couvre les fonctionnalités de base de l'application de conception d'arcades dentaires. Pour plus d'informations ou pour signaler des problèmes, veuillez consulter la documentation ou contacter l'équipe de développement.
