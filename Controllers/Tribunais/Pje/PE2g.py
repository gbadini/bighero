from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DE PE DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class PE2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjpe.jus.br/2g/login.seam"
        self.pagina_busca = "https://pje.tjpe.jus.br/2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
