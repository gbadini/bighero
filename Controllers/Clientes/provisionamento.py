from Controllers.Clientes._cliente import *
from Models.pagamentoModel import *
from Models.arquivoModel import *

# CLASSE DO LANÇAMENTO DE PROVISIONAMENTO
class ProvisionamentoCliente(Cliente):

    def __init__(self):
        super().__init__()

    # GERENCIA O LANÇAMENTO DAS ATAS
    def varrer(self, db, login, senha):
        url_remoto, url_arquivos = self.format_paths(db)

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
                query_and = query_and + " pag_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='Provisionamento')
            for proc in procs:
                try:
                    print('proc', proc)

                    pags_mesma_janela = Pagamento.select_by_provisionamento(self.conn[db], proc['prc_id'], proc['pag_jan_id'])
                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)

                    numero_busca = proc[self.campo_busca]
                    busca = self.busca_processo(numero_busca)

                    if proc['pag_valor_op'] is None:
                        raise FatalException('Valor Operacional Vazio', self.uf, self.plataforma, self.prc_id)

                    if not busca:
                        raise FatalException('Removido da Base', self.uf, self.plataforma, self.prc_id)

                    status = self.captura_status()
                    if status in ('Arquivo Morto', 'Inativo', 'Encerrado', 'Morto'):
                        raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)

                    if status == 'Pendente Citação':
                        raise FatalException('Processo Pendente Citação', self.uf, self.plataforma, self.prc_id)

                    arquivos = Arquivo.select_by_pagamento(self.conn[db], proc['pag_id'], ignora_guias=True)
                    if len(arquivos) == 0:
                        raise FatalException('Provisionamento sem Arquivos', self.uf, self.plataforma, self.prc_id)

                    for arq in arquivos:
                        if not self.confere_existencia_arquivo(url_arquivos, url_remoto, arq['arq_url']):
                            raise FatalException('Arquivo não localizado', self.uf, self.plataforma, self.prc_id)

                    if self.lanca_provisao(self.conn[db], proc, pags_mesma_janela, arquivos, url_arquivos):
                        Pagamento.update(self.conn[db], proc['pag_id'], {'pag_provisionado': True, 'pag_erro':None})
                    else:
                        if self.lanca_provisao(self.conn[db], proc, pags_mesma_janela, arquivos, url_arquivos):
                            Pagamento.update(self.conn[db], proc['pag_id'], {'pag_provisionado': True, 'pag_erro':None})

                    print('finalizado')

                except MildException:
                    tb = traceback.format_exc()
                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})

                    f1 = tb.find("Contingencia Indisponível")
                    f2 = tb.find("Erro na Reversão")
                    if f1 > -1 or f2 > -1:
                        Pagamento.update(self.conn[db], proc['pag_id'], {'pag_provisionado': True, 'pag_erro': 'Provisionamento: Não foi possível realizar a reversão'})

                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['prc_id']))

                    f = tb.find('FatalException:')
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_erro': 'Provisionamento: '+tb[f + 15:].strip()})
                    continue

        return True