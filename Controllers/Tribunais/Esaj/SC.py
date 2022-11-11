from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO SC. HERDA OS METODOS DA CLASSE ESAJ
class SC(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjsc.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjsc.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjsc.jus.br/cpopg/open.do?gateway=true"
        self.pagina_processo = "https://esaj.tjsc.jus.br/cpopg/show.do?processo.codigo="
        self.intervalo = 5