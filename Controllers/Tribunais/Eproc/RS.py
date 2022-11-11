from Controllers.Tribunais.Eproc._eproc import *


# CLASSE DA VARREDURA DO EPROC DO RS. HERDA OS METODOS DA CLASSE EPROC
class RS(Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1g.tjrs.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TJRS&sigla_sistema=Eproc"
        self.intervalo = 8
        self.reiniciar_navegador = False


from Controllers.Tribunais.Eproc._eproc2g import *


# CLASSE DA VARREDURA DO EPROC DO RS DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE EPROC2g
class RS2g(Eproc2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1g.tjrs.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TJRS&sigla_sistema=Eproc"
        self.pagina_inicial_2g = "https://eproc2g.tjrs.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TJRS&sigla_sistema=Eproc"
        self.intervalo = 8
        self.ordem_usuario = 0
        self.reiniciar_navegador = False
