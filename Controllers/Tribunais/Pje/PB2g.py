from Controllers.Tribunais.Pje._pje2g import *

# CLASSE DA VARREDURA DO PJE DA PB DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class PB2g(Pje2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjpb.jus.br/pje2g/login.seam"
        self.pagina_busca = "https://pje.tjpb.jus.br/pje2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
