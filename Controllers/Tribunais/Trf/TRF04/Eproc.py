from Controllers.Tribunais.Eproc._eproc import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class Eproc_TRF04(Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc.trf4.jus.br/eproc2trf4/"
