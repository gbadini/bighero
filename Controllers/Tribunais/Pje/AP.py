from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DA BA. HERDA OS METODOS DA CLASSE PJE
class AP(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjap.jus.br/1g/login.seam"
        self.pagina_busca = "https://pje.tjap.jus.br/1g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"