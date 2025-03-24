import os
import sys
import subprocess
import platform
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_existing_environments():
    """Clean up any existing virtual environments"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    venv_paths = [
        os.path.join(base_path, '.venv'),
        os.path.join(base_path, 'venv')
    ]
    
    for path in venv_paths:
        if os.path.exists(path):
            logging.info(f"Removing virtual environment at: {path}")
            try:
                shutil.rmtree(path, ignore_errors=False)
            except Exception as e:
                logging.warning(f"Failed to remove {path}: {e}")
                logging.info("Please try to remove the directory manually")
                sys.exit(1)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info >= (3, 12):
        logging.error("Python 3.12+ detected. This project requires Python 3.8-3.11 for better compatibility.")
        logging.info("Please install Python 3.11 or lower and try again.")
        sys.exit(1)

def setup_environment():
    """Setup virtual environment and install dependencies"""
    check_python_version()
    venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.venv'))
    requirements_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))
    
    if not os.path.exists(requirements_path):
        logging.error(f"requirements.txt not found at: {requirements_path}")
        sys.exit(1)
    
    try:
        clean_existing_environments()
        
        logging.info(f"Creating new virtual environment at: {venv_path}")
        subprocess.run([sys.executable, '-m', 'venv', venv_path], 
                      check=True,
                      capture_output=True,
                      text=True)
        
        # Get the correct pip and python paths
        if platform.system() == "Windows":
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
            pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
        else:
            python_path = os.path.join(venv_path, 'bin', 'python')
            pip_path = os.path.join(venv_path, 'bin', 'pip')
        
        # Verify environment
        if not all(os.path.exists(p) for p in [python_path, pip_path]):
            raise RuntimeError("Virtual environment creation failed - executables not found")
            
        logging.info("Upgrading pip and installing build dependencies...")
        subprocess.run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip_path, 'install', '--upgrade', 'setuptools', 'wheel', 'pip'], check=True)
        
        logging.info("Installing numpy separately first...")
        subprocess.run([
            pip_path, 'install',
            '--no-cache-dir',
            '--prefer-binary',
            'numpy>=1.21.0,<1.25.0'
        ], check=True)
        
        logging.info("Installing remaining requirements...")
        subprocess.run([
            pip_path, 'install',
            '--no-cache-dir',
            '--prefer-binary',
            '-r', requirements_path
        ], check=True)
        
        logging.info("Setup completed successfully!")
        print("\nTo activate the virtual environment:")
        if platform.system() == "Windows":
            print("Run: .venv\\Scripts\\activate")
        else:
            print("Run: source .venv/bin/activate")
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e.cmd}\nOutput: {e.output if hasattr(e, 'output') else 'No output'}")
        logging.error("Try running: python -m pip install --upgrade setuptools wheel")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_environment()
