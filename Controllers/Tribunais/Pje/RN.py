from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO RN. HERDA OS METODOS DA CLASSE PJE
class RN(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje1g.tjrn.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje1g.tjrn.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
