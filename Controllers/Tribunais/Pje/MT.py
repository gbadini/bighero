from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO MT. HERDA OS METODOS DA CLASSE PJE
class MT(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjmt.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjmt.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"