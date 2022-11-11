from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DO RJ DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class RJ2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://tjrj.pje.jus.br/2g/login.seam"
        self.pagina_busca = "https://tjrj.pje.jus.br/2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
