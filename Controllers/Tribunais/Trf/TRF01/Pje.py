from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class Pje_TRF01(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje1g.trf1.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje1g.trf1.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
