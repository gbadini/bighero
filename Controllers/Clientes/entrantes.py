from Controllers.Clientes._cliente import *
from Models.diarioprocessoModel import DiarioProcesso
from Models.contingenciaModel import Contingencia
import json

# CLASSE DA VARREDURA DE ENTRANTES. HERDA OS METODOS DA CLASSE CLIENTE
class EntrantesCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 1
        self.processos_novos = []
        self.processos_contingencia = []
        self.captura_ocorrencia = False

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha):
        self.driver.get(self.pagina_inicial)
        try:
            if not self.login(login, senha, db):
                return False
        except:
            tb = traceback.format_exc()
            print(tb)
            print('Erro no Login')
            time.sleep(60)
            return False

        self.logger.info('Login realizado')
        create_folder(self.pasta_download)
        try:
            self.pesquisa_processos(self.conn[db], self.captura_ocorrencia)
            for pn in self.processos_novos:
                print('Vinculando processo ' + pn['prc_sequencial'] + ' - ' + pn['prc_numero'])

                print('Vinculando diários')
                prc_id = Processo.get_processos_by_sequencial(self.conn[db], [pn['prc_sequencial'],])
                DiarioProcesso.vincular_by_processo(self.conn[db], pn['prc_numero'], prc_id[0]['prc_id'])

            for pc in self.processos_contingencia:
                print('Vinculando contingencia do processo '+pc['prc_sequencial'])
                prc_id = Processo.get_processos_by_sequencial(self.conn[db], [pc['prc_sequencial'], ])
                nao_lancados = Contingencia.select_by_data_citacao(self.conn[db], prc_id[0]['prc_id'], pc['ctg_data_citacao'])

                ctg_valor_possivel = prc_id[0]['prc_valor_causa']
                ctg_valor_possivel = valor_br(ctg_valor_possivel.strip()) if ctg_valor_possivel is not None and ctg_valor_possivel.strip() != '' else 0

                if len(nao_lancados) == 0:
                    Contingencia.insert(self.conn[db], [{'ctg_prc_id': prc_id[0]['prc_id'], 'ctg_valor_possivel': ctg_valor_possivel, 'ctg_valor_remoto': 0, 'ctg_data_citacao': pc['ctg_data_citacao']},])
                else:
                    if nao_lancados[0]['ctg_data_citacao'] is None:
                        dados_ups = {'ctg_data_citacao': pc['ctg_data_citacao'], }
                        if nao_lancados[0]['ctg_valor_possivel'] == 0:
                            dados_ups['ctg_valor_possivel'] = ctg_valor_possivel
                        Contingencia.update(self.conn[db], nao_lancados[0]['ctg_id'], dados_ups)

        except MildException:
            tb = traceback.format_exc()
            # print(tb)
            self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
            return False

        except CriticalException:
            tb = traceback.format_exc()
            self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
            return False

        return True

    def pesquisa_processos(self, base, captura_ocorrencia=True):
        return []

    # RETORNA A DATA ATUAL, E A DE 7 DIAS ATRÁS NO FORMATO STR
    def formata_datas(self, retroativo=7, adiante=7):
        dia_inicial = str(datetime.strftime(datetime.now() - timedelta(retroativo), '%d/%m/%Y'))
        data_atual = str(datetime.strftime(date.today() + timedelta(adiante), '%d/%m/%Y'))

        print("Dataini: ", dia_inicial, " DataFim: ", data_atual)
        return dia_inicial, data_atual