from Controllers.Clientes._cliente import *
from Models.arquivoModel import *
from Models.pagamentoModel import *

# CLASSE DO LANÇAMENTO DE PAGAMENTOS
class PagamentosCliente(Cliente):

    def __init__(self):
        super().__init__()

    # GERENCIA O LANÇAMENTO DAS ATAS
    def varrer(self, db, login, senha):
        url_remoto, url_arquivos = self.format_paths(db)
        print('url_arquivos', url_arquivos)

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
        # conferir_id = []
        while len(procs) > 0:
            query_and = self.query_and
            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                query_and = ''
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " pag_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='Pagamentos')
            for proc in procs:
                lancado = Pagamento.select_lancado(self.conn[db], proc['pag_id'])
                if len(lancado) > 0:
                    continue

                pags_mesmo_prazo = Pagamento.select_by_prazo(self.conn[db], proc['prc_id'], proc['pag_prazo'])
                len_pag_mesmo_prazo = len(pags_mesmo_prazo)
                # if len_pag_mesmo_prazo > 1:
                #     continue
                self.prc_id = proc['prc_id']
                try:
                    print('proc', proc)

                    # ABRE A PÁGINA DE BUSCA
                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)

                    numero_busca = proc[self.campo_busca]
                    busca = self.busca_processo(numero_busca)

                    # CONFERE SE O PROCESSO AINDA EXISTE NA BASE
                    if not busca:
                        raise FatalException('Removido da Base', self.uf, self.plataforma, self.prc_id)

                    # CONFERE SE O PROCESSO ESTÁ ATIVO
                    status = self.captura_status()
                    if status in ('Arquivo Morto', 'Inativo', 'Encerrado', 'Morto'):
                        raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)

                    lancado = Pagamento.select_lancado(self.conn[db], proc['pag_id'])
                    if len(lancado) > 0:
                        continue

                    # ALTERA O STATUS SUBINDO PARA TRUE PARA EVITAR LANÇAMENTOS DUPLICADOS
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': True,})

                    # TRATA OS DADOS DO PAGAMENTO DE ACORDO COM O FORMATO DO SISTEMA CLIENTE
                    dados_lanc = self.tratar_dados(self.conn[db], proc)
                    lanca_arquivos = proc['pag_tipo'] != 'Recolhimento Exclusivo de Tributos' and proc['pag_tipo'] != 'Imposto de Renda'

                    # CONFERE SE OS ARQUIVOS EXISTEM
                    for arq in dados_lanc['arquivos_ocorrencia']:
                        if not self.confere_existencia_arquivo(url_arquivos, url_remoto, arq['arq_url']):
                            raise FatalException('Arquivo não localizado', self.uf, self.plataforma, self.prc_id)

                    # CONFERE SE O PAGAMENTO JÁ ESTÁ LANÇADO
                    if self.confere_lancamento(dados_lanc, range_data_evento=0, confere_conteudo=True, quantidade=len_pag_mesmo_prazo, ignora_cancelado=True):
                        # SE FOR UM PAGAMENTO DE TRIBUTOS OS ARQUIVOS SÃO LANÇADOS COMO COMENTÁRIOS
                        if not lanca_arquivos:
                            coment = self.confere_arquivo_comentario(dados_lanc, range_data_evento=0)
                            if coment.is_integer():
                                self.lanca_arquivo_comentario(dados_lanc, url_arquivos, coment)
                                Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None})

                        # LANÇA PETIÇÃO CASO NECESSARIO E FINALIZA O LANÇAMENTO
                        if self.lanca_peticao(db, proc):
                            continue

                    # REALIZA O LANÇAMENTO DA OCORRÊNCIA
                    if not self.lanca_ocorrencia(dados_lanc, url_arquivos, gera_exception=True, lanca_arquivos=lanca_arquivos):
                        raise FatalException('Tipo não localizado', self.uf, self.plataforma, self.prc_id)

                    # SE FOR UM PAGAMENTO DE TRIBUTOS OS ARQUIVOS SÃO LANÇADOS COMO COMENTÁRIOS
                    if not lanca_arquivos:
                        coment = self.confere_arquivo_comentario(dados_lanc, range_data_evento=0)
                        if coment.is_integer():
                            self.lanca_arquivo_comentario(dados_lanc, url_arquivos, coment)

                    # CONFERE SE O PAGAMENTO FOI LANÇADO CORRETAMENTE
                    if self.confere_lancamento(dados_lanc, range_data_evento=0, confere_conteudo=True, quantidade=len_pag_mesmo_prazo, ignora_cancelado=True):
                        # SE FOR UM PAGAMENTO DE TRIBUTOS CONFERE SE EXISTE UM COMENTÁRIO NA OCORRÊNCIA
                        if not lanca_arquivos:
                            coment = self.confere_arquivo_comentario(dados_lanc, range_data_evento=0)
                            if not coment:
                                raise MildException('Ocorrência não localizada (arquivo)', self.uf, self.plataforma, self.prc_id)
                            if coment.is_integer():
                                raise MildException('Anexo não lançado', self.uf, self.plataforma, self.prc_id)

                        # LANÇA PETIÇÃO CASO NECESSARIO E FINALIZA O LANÇAMENTO
                        self.lanca_peticao(db, proc)

                    else:
                        raise MildException('Ocorrência não localizada', self.uf, self.plataforma, self.prc_id)

                    # conferir_id.append(str(proc['pag_id']))
                    print('finalizado')

                except MildException:
                    tb = traceback.format_exc()
                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None})
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None})
                    return False

                except FatalException:
                    tb = traceback.format_exc(limit=1)
                    if tb.find('O campo marcado com') > -1 and tb.find('deve ser preenchido') > -1:
                        Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None})
                        return False

                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['pag_id']))
                    f = tb.find('FatalException:')
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None, 'pag_erro': tb[f + 15:].strip()})
                    continue

                except:
                    Pagamento.update(self.conn[db], proc['pag_id'], {'pag_subindo': None})
                    raise

        # if len(conferir_id) > 0:
        #     raise CriticalException('Reiniciando navegador para conferir lançamentos', self.uf, self.plataforma, self.prc_id)

        return True

    def lanca_peticao(self, db, proc):
        config = pagamento_base(db)
        dados = {'pag_subindo': False, 'pag_lancado': True, 'pag_erro': None, 'pag_data_lancamento':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        restricao = self.check_restricao_peticao()

        if not config['peticao'] or restricao:
            Pagamento.update(self.conn[db], proc['pag_id'], dados)
            return True

        dados_lanc_pet = self.tratar_dados_peticao(self.conn[db], proc)
        if self.confere_lancamento(dados_lanc_pet, range_data_evento=1):
            Pagamento.update(self.conn[db], proc['pag_id'], dados)
            return True

        if not self.lanca_ocorrencia(dados_lanc_pet):
            # Pagamento.update(self.conn[db], proc['pag_id'], dados)
            # return True
            raise FatalException('Tipo não localizado', self.uf, self.plataforma, self.prc_id)

        if self.confere_lancamento(dados_lanc_pet, range_data_evento=1):
            Pagamento.update(self.conn[db], proc['pag_id'], dados)
            return True

        return False

    def check_restricao_peticao(self):
        return False

