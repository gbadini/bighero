from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DO RN DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class RN2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://esaj.tjrn.jus.br/sajcas/login?service=http%3A%2F%2Fesaj.tjrn.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "http://esaj.tjrn.jus.br/cposg/"
        self.pagina_processo = "http://esaj.tjrn.jus.br/cpo/sg/show.do?processo.codigo="
        self.id_mensagem_erro = "spwTabelaMensagem"