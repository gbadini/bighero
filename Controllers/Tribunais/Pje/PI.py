from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DE PI. HERDA OS METODOS DA CLASSE PJE
class PI(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://tjpi.pje.jus.br/1g/login.seam"
        self.pagina_busca = "https://tjpi.pje.jus.br/1g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
