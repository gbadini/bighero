from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO MT DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class MT2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje2.tjmt.jus.br/pje2/login.seam"
        self.pagina_busca = "https://pje2.tjmt.jus.br/pje2/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
