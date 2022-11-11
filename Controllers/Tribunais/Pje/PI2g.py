from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO PI DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class PI2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://tjpi.pje.jus.br/2g/login.seam"
        self.pagina_busca = "https://tjpi.pje.jus.br/2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
