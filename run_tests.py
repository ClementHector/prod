#!/usr/bin/env python3
"""
Script pour exécuter les tests du projet.
"""
import os
import sys
import subprocess
import argparse


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Exécute les tests pour Prod CLI")
    
    # Arguments optionnels
    parser.add_argument('test_path', nargs='?', default='tests',
                        help='Chemin des tests à exécuter (défaut: tests)')
    parser.add_argument('--unit', action='store_true',
                        help='Exécuter uniquement les tests unitaires')
    parser.add_argument('--functional', action='store_true',
                        help='Exécuter uniquement les tests fonctionnels')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mode verbeux')
    parser.add_argument('--no-cov', action='store_true',
                        help='Désactiver le rapport de couverture')
    
    return parser.parse_args()


def main():
    """Exécute les tests avec pytest."""
    args = parse_arguments()
    
    # Déterminer le chemin des tests à exécuter
    if args.unit:
        test_path = os.path.join('tests', 'unittest')
    elif args.functional:
        test_path = os.path.join('tests', 'functional')
    else:
        test_path = args.test_path
    
    # Options pour pytest
    pytest_args = ['pytest']
    
    # Ajouter le chemin des tests
    pytest_args.append(test_path)
    
    # Options supplémentaires
    if not args.no_cov:
        pytest_args.extend(['--cov=src', '--cov-report=term-missing'])
    
    if args.verbose:
        pytest_args.append('-v')
    
    # Ajouter les arguments supplémentaires passés au script
    extra_args = [arg for arg in sys.argv[1:] 
                 if arg != '--unit' and arg != '--functional' 
                 and arg != '-v' and arg != '--verbose'
                 and arg != '--no-cov'
                 and arg != args.test_path]
    
    pytest_args.extend(extra_args)
    
    # Afficher la commande
    print(f"Exécution de : {' '.join(pytest_args)}")
    
    # Exécuter pytest
    result = subprocess.run(pytest_args)
    
    # Retourner le code de sortie de pytest
    return result.returncode


if __name__ == "__main__":
    sys.exit(main()) 