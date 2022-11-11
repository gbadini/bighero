from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO PA. HERDA OS METODOS DA CLASSE PJE
class PA(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://pje.tjpa.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.tjpa.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
        self.intervalo = 7