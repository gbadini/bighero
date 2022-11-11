from Controllers.varredura import *
from Models.audienciaModel import *
from Models.acompanhamentoModel import *
from Models.parteModel import *
from Models.processoArquivoModel import *
import wget

# CLASSE PRINCIPAL DA VARREDURA
class Cliente(Varredura):
    # METODO CONSTRUTOR
    def __init__(self):
        super().__init__()
        self.campo_busca = 'prc_numero'
        self.baixar = True
        self.uf = '*'
        self.reiniciar_varredura = True

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha, token=None):
        campo_data = 'prc_data_update1'

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)

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

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        while len(procs) > 0:
            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=self.query_and, intervalo=self.range, arquivo_morto=self.arquivo_morto)
            if len(procs) == 0:
                # CONFERE SE FORA DA THREAD TEM ALGUM PROCESSO QUE AINDA NÃO FOI VARRIDO
                procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=self.query_and, intervalo=[], arquivo_morto=self.arquivo_morto)

            inicio = time.time()
            for proc in procs:
                print('proc', proc)
                if Processo.ultimo_update(self.conn[db], proc['prc_id'], self.plataforma, proc[campo_data], cliente=True):
                    print('Processo já varrido')
                    continue

                if self.intervalo > 0:
                    tempo_total = time.time() - inicio
                    if tempo_total < self.intervalo:
                        time.sleep(self.intervalo-tempo_total)
                    inicio = time.time()

                self.prc_id = proc['prc_id']
                print('prc_id ', proc['prc_id'])
                print(self.campo_busca, proc[self.campo_busca])
                self.logger.info('Varrendo Processo', extra={'log_prc_id': self.prc_id})

                try:
                    self.fecha_processo()
                    numero_busca = proc[self.campo_busca]
                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        if proc['prc_situacao'] is not None and proc['prc_situacao'] == 'Ativo Provisório':
                            Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, {}, cliente=True)
                        else:
                            Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, {'prc_situacao': 'Removido da Base'}, cliente=True)
                        # print('Removido da Base')
                        continue

                    # CRIA PASTAS PARA ARMAZENAR OS DOWNLOADS
                    pasta_intermediaria = self.pasta_intermediaria + '\\' + str(proc['prc_id'])
                    if self.baixar:
                        create_folder(self.pasta_download, pasta_intermediaria)

                    adc, prt, prc, acp, arq = self.ordem_captura(proc, db, pasta_intermediaria)

                    print('acp ',acp)
                    print('adc ',adc)
                    print('prt ',prt)
                    print('prc ',prc)
                    print('arq ', arq)

                    if Processo.ultimo_update(self.conn[db], proc['prc_id'], self.plataforma, proc[campo_data], cliente=True):
                        continue

                    Audiencia.insert(self.conn[db], proc['prc_id'], adc)
                    acps_id = Acompanhamento.insert(self.conn[db], proc['prc_id'], self.plataforma, None, acp)
                    Parte.insert(self.conn[db], proc['prc_id'], prt, self.plataforma, self.apagar_partes_inexistentes)
                    Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, prc, cliente=True)

                    if self.baixar and len(arq) > 0:
                        # SE FOR PARA FAZER DOWNLOAD, CRIA A PASTA DE DESTINO
                        target_dir = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)
                        target_dir_local = 'C:\\Downloads\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)
                        # target_dir = 'C:\\Downloads\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)

                        for ar in arq:
                            if str(ar['pra_acp_id']).find('tmp') > -1:
                                for a_id in acps_id:
                                    if a_id == ar['pra_acp_id']:
                                        ar['pra_acp_id'] = acps_id[a_id]
                                        break


                        ProcessoArquivo.insert(self.conn[db], arq)
                        try:
                            if not os.path.isdir(target_dir):
                                os.makedirs(target_dir)

                            move_arquivos(pasta_intermediaria, target_dir)
                        except:
                            if not os.path.isdir(target_dir_local):
                                os.makedirs(target_dir_local)

                            move_arquivos(pasta_intermediaria, target_dir_local)


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
                    ignorar_id.append(str(proc['prc_id']))
                    continue

        if self.query_and != '':
            print('finalizando')
            return True

        print('atualizando')
        Plataforma.update(self.conn[db], self.plataforma, self.uf)
        if self.reiniciar_varredura:
            return False

        return True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc, db, pasta_intermediaria):

        prc = self.dados(proc, self.conn[db])
        prt = self.partes()
        acp, arq = self.acompanhamentos(proc, True, self.conn[db], pasta_intermediaria)
        adc = self.audiencias()

        return adc, prt, prc, acp, arq

    def confere_existencia_arquivo(self, url_arquivo, url_remoto, filename):

        filename = filename.replace('//', '/')

        full_path = trata_path(url_arquivo + filename)
        # print(full_path)
        if os.path.isfile(full_path):
            return True

        path_site = trata_path(url_remoto + filename, True)
        # print(path_site)

        f = full_path.rfind('/')
        if f == -1:
            f = full_path.rfind('\\')
        pasta = full_path[:f]
        print(pasta)
        create_folder(pasta, clear_if_exists=False)
        try:
            wget.download(path_site, full_path)
        except:
            tb = traceback.format_exc()
            print(tb)
            return False

        return True

    # FORMATA O CAMINHO DOS ARQUIVOS
    def format_paths(self, db):
        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        server_path = config.get('arquivos', 'server_path')
        url_arquivos = config.get('arquivos', 'server_'+db)
        url_remoto = 'https://www.titaniumsys.com.br/' + url_arquivos + '/'
        url_arquivos = server_path + '\\' + url_arquivos + '\\'
        return url_remoto, url_arquivos

    # CAPTURA O STATUS ATUAL DO PROCESSO
    def captura_status(self):
        pass