from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class TRF01(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje1g.trf1.jus.br/pje/login.seam"
        self.pagina_busca = "https://pje.trt1.jus.br/primeirograu/Painel/painel_usuario/advogado.seam"