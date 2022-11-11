from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO MS. HERDA OS METODOS DA CLASSE ESAJ
class MS(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjms.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjms.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjms.jus.br/cpopg5/open.do?gateway=true"
        self.pagina_processo = "https://esaj.tjms.jus.br/cpopg5/show.do?processo.codigo="
