from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO CE. HERDA OS METODOS DA CLASSE ESAJ
class CE(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjce.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjce.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjce.jus.br/cpopg/open.do?gateway=true"
        self.pagina_processo = "https://esaj.tjce.jus.br/cpopg/show.do?processo.codigo="
