from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO MA DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class MA2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje2.tjma.jus.br/pje2g/login.seam"
        self.pagina_busca = "https://pje2.tjma.jus.br/pje2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
