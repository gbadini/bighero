from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO ES. HERDA OS METODOS DA CLASSE PJE
class ES(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjes.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjes.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
