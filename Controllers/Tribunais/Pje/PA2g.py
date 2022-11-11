from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO PA DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class PA2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjpa.jus.br/pje-2g/login.seam"
        self.pagina_busca = "https://pje.tjpa.jus.br/pje-2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
