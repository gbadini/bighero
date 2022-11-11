from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO MA. HERDA OS METODOS DA CLASSE PJE
class MA(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjma.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjma.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
