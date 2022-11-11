from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DE PE. HERDA OS METODOS DA CLASSE PJE
class PE(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjpe.jus.br/1g/login.seam"
        self.pagina_busca = "https://pje.tjpe.jus.br/1g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"

