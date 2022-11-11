from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DE RO DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class RO2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pjesg.tjro.jus.br/login.seam"
        self.pagina_busca = "https://pjesg.tjro.jus.br/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
        self.tempo_nao_iniciado_download = 20