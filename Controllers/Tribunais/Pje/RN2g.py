from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO PI DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class RN2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje2g.tjrn.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje2g.tjrn.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
