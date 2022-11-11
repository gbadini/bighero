from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO RJ. HERDA OS METODOS DA CLASSE PJE
class RJ(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://tjrj.pje.jus.br/1g/login.seam"
        self.pagina_busca = "https://tjrj.pje.jus.br/1g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
