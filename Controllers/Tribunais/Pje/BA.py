from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DA BA. HERDA OS METODOS DA CLASSE PJE
class BA(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjba.jus.br/pje-web/login.seam"
        self.pagina_busca = "https://pje.tjba.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"