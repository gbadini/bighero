from Controllers.Tribunais.Pje._pje import *
import win32gui
import win32con
import win32api

# CLASSE DA VARREDURA DO PJE DE RO. HERDA OS METODOS DA CLASSE PJE
class RO(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://pje.tjro.jus.br/pg/login.seam"
        self.pagina_busca = "https://pjepg.tjro.jus.br/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
        self.tempo_nao_iniciado_download = 20