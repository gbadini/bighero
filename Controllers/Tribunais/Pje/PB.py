from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DA PB. HERDA OS METODOS DA CLASSE PJE
class PB(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjpb.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjpb.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"