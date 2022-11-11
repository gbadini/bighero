from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO RN. HERDA OS METODOS DA CLASSE ESAJ
class RN(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://esaj.tjrn.jus.br/sajcas/login?service=http%3A%2F%2Fesaj.tjrn.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "http://esaj.tjrn.jus.br/cpo/pg/open.do"
        self.pagina_processo = "http://esaj.tjrn.jus.br/cpo/pg/show.do?processo.codigo="
        self.url_base = "http://esaj.tjrn.jus.br/"
        self.id_mensagem_erro = "spwTabelaMensagem"
        self.download_click = True