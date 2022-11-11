from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DE AL. HERDA OS METODOS DA CLASSE ESAJ
class AL(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://www2.tjal.jus.br/sajcas/login?service=https%3A%2F%2Fwww2.tjal.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://www2.tjal.jus.br/cpopg/open.do?gateway=true"
        self.pagina_processo = "https://www2.tjal.jus.br/cpopg/show.do?processo.codigo="
