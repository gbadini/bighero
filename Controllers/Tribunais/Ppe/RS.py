from Controllers.Tribunais.Ppe._ppe import *


# CLASSE DA VARREDURA DO EPROC DO RS. HERDA OS METODOS DA CLASSE PPE
class RS(Ppe):

    def __init__(self):
        super().__init__()
        self.apagar_partes_inexistentes = False
        self.tratar_tamanhos = True
        self.pagina_inicial = "https://ppe.tjrs.jus.br/ppe/signin"
