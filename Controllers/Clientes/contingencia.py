from Controllers.Clientes._cliente import *
from Models.contingenciaModel import *

# CLASSE DO LANÇAMENTO DE CONTINGENCIA
class ContingenciaCliente(Cliente):

    def __init__(self):
        super().__init__()

    # GERENCIA O LANÇAMENTO DAS ATAS
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

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        last_id = 0
        while len(procs) > 0:
            query_and = self.query_and
            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                query_and = ''
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " ctg_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='Contingencia')
            for proc in procs:
                try:
                    print('proc', proc)

                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)

                    numero_busca = proc[self.campo_busca]
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        Contingencia.update(self.conn[db], proc['ctg_id'], {'ctg_erro': 'Removido da Base'})
                        raise FatalException('Removido da Base', self.uf, self.plataforma, self.prc_id)

                    # CONFERE SE O PROCESSO ESTÁ ATIVO
                    status = self.captura_status()
                    if status != proc['prc_situacao']:
                        Processo.update_simples(self.conn[db], proc['prc_id'], {'prc_data_update1': None})

                    if status in ('Arquivo Morto', 'Inativo', 'Encerrado', 'Morto'):
                        raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)

                    # CONFERE SE O PROCESSO ESTÁ PENDENTE CITAÇÂO
                    # status = self.captura_status()
                    if status in ('Pendente Citação',):
                        raise FatalException('Processo Pendente Citação', self.uf, self.plataforma, self.prc_id)


                    if self.lanca_contingencia(proc):
                        Contingencia.update(self.conn[db], proc['ctg_id'], {'ctg_lancado': True, 'ctg_erro': None, 'ctg_data_lancamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    else:
                        if self.lanca_contingencia(proc):
                            Contingencia.update(self.conn[db], proc['ctg_id'], {'ctg_lancado': True, 'ctg_erro': None, 'ctg_data_lancamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

                    print('finalizado')

                except MildException:
                    tb = traceback.format_exc()
                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['ctg_id']))

                    f = tb.find('Pendente Citação')
                    if f == -1:
                        f = tb.find('FatalException:')
                        Contingencia.update(self.conn[db], proc['ctg_id'], {'ctg_erro': tb[f + 15:].strip()})

                    continue

        return True