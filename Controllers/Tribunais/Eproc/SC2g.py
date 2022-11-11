from Controllers.Tribunais.Eproc._eproc2g import *


# CLASSE DA VARREDURA DO EPROC DE SC DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE EPROC2g
class SC2g(Eproc2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TJSC&sigla_sistema=Eproc"
        self.pagina_inicial_2g = "https://eproc2g.tjsc.jus.br/eproc/externo_controlador.php?acao=principal"
        self.intervalo = 7
        self.ordem_usuario = 0