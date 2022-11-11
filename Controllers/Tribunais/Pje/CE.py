from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class CE(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjce.jus.br/pje1grau/login.seam"
        self.pagina_busca = "https://pje.tjce.jus.br/pje1grau/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
