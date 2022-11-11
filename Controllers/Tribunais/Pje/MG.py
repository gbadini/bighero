from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DE MG. HERDA OS METODOS DA CLASSE PJE
class MG(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjmg.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjmg.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
