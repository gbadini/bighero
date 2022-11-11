from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO CE DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class CE2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjce.jus.br/pje2grau/login.seam"
        self.pagina_busca = "https://pje.tjce.jus.br/pje2grau/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
