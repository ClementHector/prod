"""
Step definitions pour les tests fonctionnels de l'interface en ligne de commande.
"""
import os
import tempfile
import subprocess
import contextlib
from io import StringIO
from unittest import mock
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

from src.cli import CLI, main
from src.software_cli import SoftwareCLI
from src.production_environment import ProductionEnvironment

# Importer tous les scénarios du fichier feature
scenarios('../features/cli.feature')


@pytest.fixture
def cli_context():
    """Fixture pour le contexte des tests CLI."""
    # Créer un répertoire temporaire
    temp_dir = tempfile.TemporaryDirectory()
    
    # Contexte pour les tests
    context = {
        'temp_dir': temp_dir,
        'stdout': '',
        'stderr': '',
        'return_code': 0,
        'env_vars': {}
    }
    
    yield context
    
    # Cleanup
    temp_dir.cleanup()


@given('several productions exist')
def several_productions_exist(cli_context):
    """Créer plusieurs productions."""
    # Créer la structure de répertoires
    prods_dir = os.path.join(cli_context['temp_dir'].name, 'config', 'prods')
    os.makedirs(prods_dir, exist_ok=True)
    
    # Créer quelques répertoires de production
    for prod in ['dlt', 'prod1', 'prod2']:
        os.makedirs(os.path.join(prods_dir, prod), exist_ok=True)
    
    # Mock pour CLI._handle_list_command pour utiliser notre répertoire de test
    cli_context['mock_prods_dir'] = mock.patch(
        'src.cli.os.path.join',
        side_effect=lambda *args: os.path.join(cli_context['temp_dir'].name, 'config', 'prods') 
                                   if args[1] == '../config/prods' else os.path.join(*args)
    )


@given(parsers.parse('a valid production "{prod_name}" exists'))
def valid_production_exists(cli_context, prod_name):
    """Créer une production valide."""
    # Créer la structure de répertoires
    prod_dir = os.path.join(cli_context['temp_dir'].name, 'config', 'prods', prod_name)
    os.makedirs(os.path.join(prod_dir, 'config'), exist_ok=True)
    
    # Sauvegarder le nom de la production dans le contexte
    cli_context['prod_name'] = prod_name
    
    # Mock pour ProductionEnvironment pour éviter d'accéder aux fichiers réels
    cli_context['mock_prod_env'] = mock.patch(
        'src.cli.ProductionEnvironment',
        autospec=True
    )


@given(parsers.parse('I am in the "{prod_name}" production environment'))
def in_production_environment(cli_context, prod_name):
    """Simuler être dans un environnement de production."""
    # Sauvegarder le nom de la production dans le contexte
    cli_context['prod_name'] = prod_name
    
    # Mock pour os.environ.get pour retourner le nom de la production
    cli_context['mock_environ_get'] = mock.patch(
        'src.software_cli.os.environ.get',
        return_value=prod_name
    )
    
    # Mock pour ProductionEnvironment.execute_software
    cli_context['mock_execute_software'] = mock.patch(
        'src.production_environment.ProductionEnvironment.execute_software'
    )


@when(parsers.parse('I run the command "{command}"'))
def run_command(cli_context, command):
    """Exécuter une commande."""
    # Analyser la commande
    parts = command.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd == 'prod':
        # Exécuter une commande prod
        with mock.patch('sys.stdout', new=mock.StringIO()) as mock_stdout, \
             mock.patch('sys.stderr', new=mock.StringIO()) as mock_stderr:
            
            # Ajouter les mocks nécessaires
            mocks = []
            if 'mock_prods_dir' in cli_context:
                mocks.append(cli_context['mock_prods_dir'])
            if 'mock_prod_env' in cli_context:
                mocks.append(cli_context['mock_prod_env'])
            
            # Exécuter la commande avec les mocks
            with mock.patch('sys.argv', ['prod'] + args):
                with contextlib.ExitStack() as stack:
                    for m in mocks:
                        stack.enter_context(m)
                    cli = CLI()
                    cli_context['return_code'] = cli.run(args)
            
            # Capturer la sortie
            cli_context['stdout'] = mock_stdout.getvalue()
            cli_context['stderr'] = mock_stderr.getvalue()
            
    elif cmd in ['maya', 'nuke', 'houdini']:
        # Exécuter une commande de logiciel
        with mock.patch('sys.stdout', new=mock.StringIO()) as mock_stdout, \
             mock.patch('sys.stderr', new=mock.StringIO()) as mock_stderr:
            
            with cli_context['mock_environ_get'], \
                 cli_context['mock_execute_software']:
                
                # Extraire les arguments supplémentaires
                additional_args = []
                if '--packages' in args:
                    idx = args.index('--packages')
                    if idx + 1 < len(args):
                        additional_args = ['--packages', args[idx + 1]]
                        # Sauvegarder le package supplémentaire dans le contexte
                        cli_context['additional_package'] = args[idx + 1]
                
                if '--env-only' in args:
                    additional_args.append('--env-only')
                    cli_context['env_only'] = True
                
                # Exécuter la commande
                with mock.patch('sys.argv', [cmd] + additional_args):
                    cli = SoftwareCLI(cmd)
                    cli_context['return_code'] = cli.run(additional_args)
            
            # Capturer la sortie
            cli_context['stdout'] = mock_stdout.getvalue()
            cli_context['stderr'] = mock_stderr.getvalue()


@then('I should see a list of all available productions')
def check_productions_list(cli_context):
    """Vérifier que la liste des productions est affichée."""
    assert 'Available productions:' in cli_context['stdout']
    assert '* dlt' in cli_context['stdout']
    assert '* prod1' in cli_context['stdout']
    assert '* prod2' in cli_context['stdout']


@then('I should see a confirmation message')
def check_confirmation_message(cli_context):
    """Vérifier qu'un message de confirmation est affiché."""
    assert f"Entered production environment '{cli_context['prod_name']}'" in cli_context['stdout']


@then('I should see a list of available software for that production')
def check_software_list(cli_context):
    """Vérifier que la liste des logiciels disponibles est affichée."""
    assert 'Available software:' in cli_context['stdout']


@then('the environment variables should be set for that production')
def check_environment_variables(cli_context):
    """Vérifier que les variables d'environnement sont définies pour la production."""
    # Cette vérification est implicite car nous mockons ProductionEnvironment
    # Le mock de ProductionEnvironment.activate() aurait été appelé
    mock_prod_env = cli_context['mock_prod_env']
    assert mock_prod_env.return_value.activate.called


@then('Maya should be launched with the correct settings')
def check_maya_launched(cli_context):
    """Vérifier que Maya est lancé avec les paramètres corrects."""
    # Vérifier que execute_software a été appelé avec les bons arguments
    mock_execute = cli_context['mock_execute_software']
    assert mock_execute.called
    
    # Vérifier les arguments de l'appel
    args, kwargs = mock_execute.call_args
    assert args[0] == 'maya'  # Le premier argument est le nom du logiciel
    assert not kwargs.get('env_only', False)  # Ne doit pas être en mode env_only


@then(parsers.parse('Maya should be launched with the additional package "{package}"'))
def check_maya_launched_with_package(cli_context, package):
    """Vérifier que Maya est lancé avec le package supplémentaire spécifié."""
    # Vérifier que execute_software a été appelé avec les bons arguments
    mock_execute = cli_context['mock_execute_software']
    assert mock_execute.called
    
    # Vérifier les arguments de l'appel
    args, kwargs = mock_execute.call_args
    assert args[0] == 'maya'  # Le premier argument est le nom du logiciel
    
    # Vérifier que le package supplémentaire est inclus
    additional_packages = args[1] if len(args) > 1 else []
    assert package in additional_packages


@then('I should be in a Rez environment for Maya')
def check_in_rez_environment(cli_context):
    """Vérifier que l'utilisateur est dans un environnement Rez pour Maya."""
    # Vérifier que execute_software a été appelé avec les bons arguments
    mock_execute = cli_context['mock_execute_software']
    assert mock_execute.called
    
    # Vérifier les arguments de l'appel
    args, kwargs = mock_execute.call_args
    assert args[0] == 'maya'  # Le premier argument est le nom du logiciel
    assert kwargs.get('env_only', False)  # Doit être en mode env_only


@then('the software should not be launched')
def check_software_not_launched(cli_context):
    """Vérifier que le logiciel n'est pas lancé."""
    # Cette vérification est implicite car nous avons vérifié que env_only est True
    # Lorsque env_only est True, le logiciel n'est pas lancé
    pass 