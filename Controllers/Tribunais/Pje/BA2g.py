from Controllers.Tribunais.Pje._pje2g import *


# CLASSE DA VARREDURA DO PJE DO BA DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class BA2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje2g.tjba.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje2g.tjba.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
