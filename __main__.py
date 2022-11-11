import sys
from argparse import ArgumentParser
from Config.helpers import *
from multiprocessing import Manager
from pathlib import Path

import ctypes, sys
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if is_admin():
    BASE_DIR = Path(__file__).resolve().parent
    caminho = BASE_DIR.joinpath(r'venv\Lib\site-package')
    # caminho = str(Path(__file__).resolve().parent)+'\\venv\\Lib\\site-packages'
    sys.path.append(caminho)
    # sys.path.append('C:\\Users\\gbadi\\PycharmProjects\\bighero\\venv\\Lib\\site-packages')

    if __name__ == "__main__":
        load_form()
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

