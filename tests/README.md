# Tests pour Prod CLI

Ce répertoire contient les tests pour le Prod CLI. Les tests sont organisés en deux catégories :
- **Tests unitaires** : tests de composants individuels
- **Tests fonctionnels** : tests de comportement avec pytest-bdd et Gherkin

## Prérequis

Pour exécuter les tests, vous devez installer les dépendances de test :

```bash
# Installation directe
pip install -e ".[test]"

# Ou en utilisant requirements-dev.txt
pip install -r requirements-dev.txt
```

## Structure des tests

```
tests/
├── unittest/                # Tests unitaires
│   ├── test_config_manager.py
│   ├── test_logger.py
│   └── ...
├── functional/              # Tests fonctionnels avec pytest-bdd
│   ├── features/            # Fichiers de features Gherkin
│   │   ├── configuration.feature
│   │   ├── production_environment.feature
│   │   └── cli.feature
│   └── step_defs/           # Définitions des steps
│       ├── test_configuration_steps.py
│       ├── test_production_environment_steps.py
│       └── test_cli_steps.py
└── README.md                # Ce fichier
```

## Exécution des tests

Plusieurs méthodes sont disponibles pour exécuter les tests :

### Utiliser pytest directement

```bash
# Exécuter tous les tests
pytest

# Exécuter uniquement les tests unitaires
pytest tests/unittest

# Exécuter uniquement les tests fonctionnels
pytest tests/functional

# Exécuter un test spécifique
pytest tests/unittest/test_config_manager.py

# Exécuter un scénario spécifique par mot-clé
pytest -k "configuration"
```

### Utiliser le script run_tests.py

```bash
# Exécuter tous les tests
python run_tests.py

# Exécuter uniquement les tests unitaires
python run_tests.py tests/unittest

# Exécuter uniquement les tests fonctionnels
python run_tests.py tests/functional

# Passer des arguments à pytest
python run_tests.py -xvs
```

## Tests fonctionnels avec pytest-bdd

Les tests fonctionnels utilisent pytest-bdd pour définir des scénarios de test en langage Gherkin. Chaque scénario est défini dans un fichier `.feature` et les implémentations de steps correspondantes sont dans les fichiers `test_*_steps.py`.

### Features principales

1. **Configuration management** (`configuration.feature`)
   - Gestion des fichiers de configuration
   - Hiérarchie de configuration (studio < production < user)
   - Override de configuration

2. **Production environment** (`production_environment.feature`)
   - Activation d'environnements de production
   - Création d'alias Rez
   - Lancement de logiciels avec des packages spécifiques

3. **Command line interface** (`cli.feature`)
   - Commandes CLI pour lister et entrer dans des productions
   - Exécution de logiciels avec options

## Conventions

- Les noms de fichiers de test commencent par `test_`
- Les noms de fonctions de test commencent par `test_`
- Utilisez `assert` pour les vérifications dans les tests
- Utilisez des fixtures pour la configuration et le nettoyage 