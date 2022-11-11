from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO SC. HERDA OS METODOS DA CLASSE ESAJ
class SP(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjsp.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjsp.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjsp.jus.br/cpopg/open.do?gateway=true"
        self.pagina_processo = "https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo="
