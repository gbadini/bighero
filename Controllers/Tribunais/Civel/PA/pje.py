from Controllers.Plataformas.Pje._pje import *


def PA(versao=1, grau=1):
    C = Pje(versao, grau)
    C.pagina_inicial = "http://pje.tjpa.jus.br/pje/login.seam"
    C.pagina_busca = "https://pje.tjpa.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
    C.intervalo = 7
    return C
    # self.uf = 'PA'


#
# # CLASSE DA VARREDURA DO PJE DO PA. HERDA OS METODOS DA CLASSE PJE
# class Pg(Pje(grau=1)):
#
#     def __init__(self):
#         super().__init__()
#         self.pagina_inicial = "http://pje.tjpa.jus.br/pje/login.seam"
#         self.pagina_busca = "https://pje.tjpa.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
#         self.intervalo = 7
#         self.uf = 'PA'
#
#
# # CLASSE DA VARREDURA DO PJE DO PA DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
# class Sg(Pje(grau=2)):
#
#     def __init__(self):
#         super().__init__()
#         self.pagina_inicial = "https://pje.tjpa.jus.br/pje-2g/login.seam"
#         self.pagina_busca = "https://pje.tjpa.jus.br/pje-2g/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
#         self.uf = 'PA'
