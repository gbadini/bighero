from Controllers.Clientes.entrantes import *
from Controllers.Clientes.Processum._processum import *
from Models.enderecoModel import Endereco
import pandas as pd

# CAPTURA PROCESSOS ENTRANTES DO PROCESSUM
class Entrantes(EntrantesCliente, Processum):

    def pesquisa_processos(self, base, captura_ocorrencia=True):
        self.gera_relatorio_cadastro(base, 'Cadastramento')
        self.gera_relatorio_cadastro(base, 'Data Log Citação', True, 0, 0)

        if captura_ocorrencia:
            for i in range(1, 7):
                self.gera_relatorio_cadastro(base, 'Data Log Citação', True, i, i * -1)
            self.gera_relatorio_cadastro(base, 'Cadastro Ocorrência', True)
            self.gera_relatorio_ocorrencias(base)
            self.gera_relatorio_enderecos(base)
            dia_da_semana = datetime.now().isoweekday()
            if dia_da_semana == 7:
                self.gera_relatorio_valores(base)

        # FECHA NAVEGADOR
        self.driver.close()

    def gera_relatorio_enderecos(self, base):
        self.driver.find_element_by_xpath('//*[@id="formMenu"]/table/tbody/tr/td/div/table/tbody/tr/td[1]').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="cmSubMenuID1"]/table/tbody/tr[2]/td[2]', aguarda_visibilidade=True)
        # self.driver.get('https://ww3.vivo-base.com.br/processumweb/modulo/processo/relatorios/filtroAcompanhamentoPrazos.jsf')
        self.driver.find_element_by_xpath('//*[@id="cmSubMenuID1"]/table/tbody/tr[2]/td[2]').click()
        # SELECIONA TIPO DOCUMENTO
        opcoes = Select(self.driver.find_element_by_id('body:fPesquisa:tipoDocumento'))
        opcoes.select_by_visible_text('Processo')
        # SELECIONA ESP DOCUMENTO
        opcoes = Select(self.driver.find_element_by_id('body:fPesquisa:espTipoDocumento'))
        opcoes.select_by_visible_text('Comprovante de Residência')
        # SELECIONA TIPO DATA
        opcoes = Select(self.driver.find_element_by_id('body:fPesquisa:tipoData'))
        opcoes.select_by_visible_text('Cadastro')

        # PREENCHE O CAMPO DE DATA
        intervalo_de_datas = self.formata_datas(5, 5)

        aguarda_presenca_elemento(self.driver,  "body:fPesquisa:dataInformeInicial", tipo="ID", aguarda_visibilidade=True)
        self.preenche_campo(intervalo_de_datas[0], "body:fPesquisa:dataInformeInicial", tipo="ID", limpar_string=False)
        self.preenche_campo(intervalo_de_datas[1], "body:fPesquisa:dataInformeFinal", tipo="ID", limpar_string=False)
        # FIM DO PREENCHIMENTO DE DATAS

        # CLICA PARA GERAR RELATÓRIO
        self.driver.find_element_by_id('body:fPesquisa:btActionFiltrar').click()

        # CLICA PARA EXPORTAR EXCEL
        btn_exportar = self.driver.find_element_by_id('body:fGrid:lblExportar')
        if not btn_exportar:
            return

        btn_exportar.click()

        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        xpath = '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[1]/option[1]'
        aguarda_presenca_elemento(self.driver, xpath, aguarda_visibilidade=True)
        self.driver.find_element_by_xpath(xpath).click()

        caminho_arquivo = self.baixa_planilha()
        df = pd.read_excel(caminho_arquivo)
        df = df.astype(str)
        df.fillna('')

        dados_planilha = {}
        sequenciais = []
        for index, row in df.iterrows():
            sequencial = row['PROCESSO SEQ Nº'].strip()

            prc_autor = self.trata_nomes(row['POLO ATIVO'], 80) if row['POLO ATIVO'] != 'nan' else None
            prc_numero = row['Nº PROCESSO'].strip()
            observacao = row['OBSERVACAO'].strip()
            # print('observacao',observacao)
            if observacao == '' or observacao == 'nan':
                continue

            sequenciais.append(sequencial)
            observacao = observacao.split('|')
            endereco = {}
            endereco['end_contato'] = observacao[0].strip()
            endereco['end_logradouro'] = observacao[1].strip()
            endereco['end_numero'] = observacao[2].strip()
            end_e = endereco['end_numero'].find(' e ')
            endereco['end_complemento'] = None
            if end_e > -1:
                endereco['end_complemento'] = endereco['end_numero'][end_e+2:].strip()
                endereco['end_numero'] = endereco['end_numero'][:end_e].strip()

            endereco['end_bairro'] = observacao[3].strip()
            endereco['end_cidade'] = observacao[4].strip()
            endereco['end_uf'] = observacao[5].strip()
            endereco['end_cep'] = observacao[6].replace('CEP','').strip()
            endereco['end_origem'] = observacao[7].strip()

            prc = {'prc_sequencial': sequencial, 'prc_numero': prc_numero, 'prc_autor': prc_autor,
                   'prc_numero_processum': prc_numero, 'endereco': endereco}

            dados_planilha[sequencial] = prc

        # os.remove(caminho_arquivo)

        enderecos = []
        procs_base = Processo.get_processos_by_sequencial(base, sequenciais)
        for p in procs_base:
            end = dados_planilha[p['prc_sequencial']]['endereco']
            end_base = Endereco.select(base, p['prc_id'], end['end_cep'], end['end_logradouro'], end['end_numero'])
            if len(end_base) == 0:
                end['end_prc_id'] = p['prc_id']
                enderecos.append(end)

        Endereco.insert(base, enderecos)

    def gera_relatorio_ocorrencias(self, base):
        self.driver.get('https://ww3.vivo-base.com.br/processumweb/modulo/processo/relatorios/rel_acompanhamento_cumprimento.jsf')

        # SELECIONA A OPÇÃO CADASTRAMENTO
        aguarda_presenca_elemento(self.driver, "body:fPesquisa:datas", tipo="ID", aguarda_visibilidade=True)
        opcoes = Select(self.driver.find_element_by_id('body:fPesquisa:datas'))
        opcoes.select_by_visible_text('Cumprimento')

        # PREENCHE O CAMPO DE DATA
        intervalo_de_datas = self.formata_datas(4, 3)

        aguarda_presenca_elemento(self.driver,  "body:fPesquisa:dataInicial", tipo="ID", aguarda_visibilidade=True)
        self.preenche_campo(intervalo_de_datas[0], "body:fPesquisa:dataInicial", tipo="ID", limpar_string=False)
        self.preenche_campo(intervalo_de_datas[1], "body:fPesquisa:dataFinal", tipo="ID", limpar_string=False)
        # FIM DO PREENCHIMENTO DE DATAS

        # CLICA PARA GERAR RELATÓRIO
        self.driver.find_element_by_id('body:fPesquisa:_idJsp40').click()

        # CLICA PARA EXPORTAR EXCEL
        self.driver.find_element_by_id('body:fPesquisa:exportarExcel').click()

        caminho_arquivo = self.baixa_planilha()
        df = pd.read_excel(caminho_arquivo)
        df = df.astype(str)
        df.fillna('')

        dados_planilha = {}
        sequenciais = []
        for index, row in df.iterrows():
            sequencial = row['Número Processo'].strip()
            data_ocorrencia = row['Data Prazo Legal']
            if data_ocorrencia is not None:
                dias_cumprimento = row['Dias Consumidos Cumprimento']
                if dias_cumprimento == 'nan' or data_ocorrencia == 'nan':
                    continue
                dias_cumprimento = int(float(dias_cumprimento))
                data_ocorrencia = datetime.strptime(data_ocorrencia, '%d/%m/%Y %H:%M')
                data_ocorrencia = data_ocorrencia + timedelta(dias_cumprimento)

            if sequencial in sequenciais:
                if data_ocorrencia is None:
                    continue

                if data_ocorrencia > dados_planilha[sequencial]['data_ocorrencia']:
                    dados_planilha[sequencial]['data_ocorrencia'] = data_ocorrencia

                continue

            else:
                sequenciais.append(sequencial)
                prc_autor = self.trata_nomes(row['Autor(es)'], 80) if row['Autor(es)'] != 'nan' else None
                prc_comarca = self.trata_nomes(row['Comarca'], 45) if row['Comarca'] != 'nan' else None
                prc_numero = row['Num. Processo 1ª Instância'].strip()
                carteira = self.verifica_carteira(sequencial)
                estado = tratar_estado(row['Estado']) if row['Estado'] != 'nan' else ''
                prc_objeto1 = row['Objeto Ação'].strip() if row['Objeto Ação'] != 'nan' else None
                prc_objeto2 = row['Especificação Objeto da Ação'].strip() if row['Especificação Objeto da Ação'] != 'nan' else None
                prc_objeto3 = row['Detalhe Espec. Objeto Ação'].strip() if row['Detalhe Espec. Objeto Ação'] != 'nan' else None

                cadastro = row['Data Cadastro Processo'] if row['Data Cadastro Processo'] != 'nan' else None
                if cadastro is not None:
                    cadastro = datetime.strptime(cadastro, '%d/%m/%Y %H:%M')

                prc = {'prc_sequencial': sequencial, 'prc_numero': prc_numero, 'prc_autor': prc_autor,
                       'prc_numero_processum': prc_numero, 'prc_carteira': carteira, 'prc_estado': estado,
                       'prc_comarca': prc_comarca, 'prc_objeto1': prc_objeto1, 'prc_objeto2': prc_objeto2,
                       'prc_objeto3': prc_objeto3, 'prc_data_cadastro': cadastro,
                       'prc_data': cadastro, 'data_ocorrencia': data_ocorrencia}

                dados_planilha[sequencial] = prc

        os.remove(caminho_arquivo)

        procs_base = Processo.get_processos_by_sequencial(base, sequenciais)
        sequenciais_base = {}
        for p in procs_base:
            sequenciais_base[p['prc_sequencial']] = p

        processos_novos = []
        processos_existentes = []
        # SEPARA OS PROCESSOS QUE NÃO ESTÃO NA BASE
        for seq_pln in dados_planilha:
            data_ocorrencia = dados_planilha[seq_pln]['data_ocorrencia']
            pln = dados_planilha[seq_pln]
            if seq_pln not in sequenciais_base:
                existe = False
                for pn in self.processos_novos:
                    if pn['prc_sequencial'] == seq_pln:
                        existe = True
                        break

                if existe:
                    continue

                del pln['data_ocorrencia']
                self.processos_novos.append(pln)
                processos_novos.append(pln)
            else:
                prc_data_update1 = sequenciais_base[seq_pln]['prc_data_update1']
                if prc_data_update1 is not None and prc_data_update1 < data_ocorrencia:
                    processos_existentes.append(sequenciais_base[seq_pln]['prc_id'])

        processos_novos = self.check_proc_dup(processos_novos)
        print('processos_novos: ', len(processos_novos))
        print('processos_existentes', len(processos_existentes))
        Processo.insert_batch(base, processos_novos)

        print('Iniciando update')

        if len(processos_existentes) > 0:
            Processo.update_batch(base, processos_existentes, {'prc_data_update1': None})

        print('Fim do update')

    # AGUARDA DOWNLOAD E RETORNA O NOME DO ARQUIVO
    def baixa_planilha(self, tempo_download=300):
        result_download = aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=tempo_download)
        if not result_download:
            raise CriticalException("Erro no download da planilha", self.uf, self.plataforma, self.prc_id, False)

        arquivo_xls = ""
        file_names = os.listdir(self.pasta_download)
        for f in file_names:
            if f.find('temp-') == 0 and (f.find('.xls') > -1 or f.find('.csv') > -1):
                arquivo_xls = f

        if arquivo_xls == "":
            raise CriticalException("Erro ao localizar planilha", self.uf, self.plataforma, self.prc_id, False)

        caminho_arquivo = self.pasta_download + "\\" + arquivo_xls
        # ABRIR A PLANILHA EXCEL QUE CONTEM OS DADOS
        print("caminho para abrir planilha:", caminho_arquivo)
        return caminho_arquivo

    def gera_relatorio_valores(self, base):
        self.driver.get(self.pagina_busca)
        self.driver.find_element_by_id('fPesquisa:lblBtMudarFiltro').click()
        try_click(self.driver, 'fPesquisa:_idJsp228', tipo='ID')

        sel_situacao = Select(self.driver.find_element_by_id('fPesquisa:situacao'))
        sel_situacao.select_by_visible_text('Ativo')

        sel_divisao = Select(self.driver.find_element_by_id('fPesquisa:divisaoProcesso'))
        sel_divisao.select_by_visible_text('CONSUMIDOR NACIONAL')

        # CLICA NO BOTÃO DE PESQUISAR
        self.driver.find_element_by_id('fPesquisa:_idJsp224').click()
        self.driver.execute_script("window.scrollTo(0,100)")

        msg_erro = self.driver.find_element_by_id('subviewMessages:formHeader:msgErro')
        if msg_erro and msg_erro.is_displayed():
            if msg_erro.text.find('não encontrou nenhum Processo') > -1:
                return

        # CLICA NO BOTÃO DE EXPORTAR EXCEL
        aguarda_presenca_elemento(self.driver, "fPesquisa:_idJsp245", tipo='ID', aguarda_visibilidade=True)
        self.driver.find_element_by_id('fPesquisa:_idJsp245').click()
        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        xpath = '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[7]/option[1]'
        aguarda_presenca_elemento(self.driver, xpath, aguarda_visibilidade=True)
        self.driver.find_element_by_xpath(xpath).click()
        caminho_arquivo = self.baixa_planilha(900)
        if caminho_arquivo.find('.csv') > -1:
            df = pd.read_csv(caminho_arquivo, encoding="ISO-8859-1", engine='python', on_bad_lines='skip', sep=";")
        else:
            df = pd.read_excel(caminho_arquivo)
        df = df.astype(str)
        df.fillna('')

        processos_novos = []
        for index, row in df.iterrows():
            sequencial = row['PROCESSO SEQ Nº'].strip()
            prc_autor = self.trata_nomes(row['NOME AUTOR'], 80) if row['NOME AUTOR'] != 'nan' else None
            prc_comarca = self.trata_nomes(row['COMARCA'], 45) if row['COMARCA'] != 'nan' else None
            prc_numero = row['PROCESSO 1ª INSTANCIA Nº'].replace('"','').replace('=','').strip()
            carteira = self.verifica_carteira(sequencial)
            estado = tratar_estado(row['ESTADO'])
            area = 2 if row['DIVISAO RESPONSAVEL'] == 'NACIONAL TRABALHISTA' else 1
            cadastro = row['DATA CADASTRO']
            prc_situacao = row['SITUAÇÃO'].strip() if row['SITUAÇÃO'] != 'nan' else None
            prc_objeto1 = row['OBJETO ACAO'].strip() if row['OBJETO ACAO'] != 'nan' else None
            prc_objeto2 = row['ESP OBJETO ACAO'].strip() if row['ESP OBJETO ACAO'] != 'nan' else None
            prc_objeto3 = row['DET ESP OBJETO ACAO'].strip() if row['DET ESP OBJETO ACAO'] != 'nan' else None
            prc_valor_provavel = valor_br(row['VALOR CURTO PRAZO'].strip()) if row['VALOR CURTO PRAZO'] != 'nan' else None
            prc_valor_possivel = valor_br(row['VALOR POSSÍVEL'].strip()) if row['VALOR POSSÍVEL'] != 'nan' else None
            if cadastro is not None:
                cadastro = datetime.strptime(cadastro, '%d/%m/%Y %H:%M')

            prc = {'prc_sequencial': sequencial, 'prc_numero': prc_numero, 'prc_autor': prc_autor,
                   'prc_numero_processum': prc_numero, 'prc_carteira': carteira, 'prc_estado': estado,
                   'prc_comarca': prc_comarca, 'prc_objeto1': prc_objeto1, 'prc_objeto2': prc_objeto2,
                   'prc_objeto3': prc_objeto3, 'prc_data_cadastro': cadastro, 'prc_data': cadastro,
                   'prc_area': area, 'prc_situacao': prc_situacao, 'prc_valor_provavel':prc_valor_provavel, 'prc_valor_possivel':prc_valor_possivel }

            proc_base = Processo.get_processos_by_sequencial(base, [sequencial, ])
            if len(proc_base) == 0:
                print('novo',prc)
                processos_novos.append(prc)
            else:
                print('update',{'prc_situacao': prc['prc_situacao'], 'prc_valor_provavel':prc['prc_valor_provavel'], 'prc_valor_possivel':prc['prc_valor_possivel']})
                Processo.update_simples(base, proc_base[0]['prc_id'], {'prc_situacao': prc['prc_situacao'], 'prc_valor_provavel':prc['prc_valor_provavel'], 'prc_valor_possivel':prc['prc_valor_possivel']})

        os.remove(caminho_arquivo)
        processos_novos = self.check_proc_dup(processos_novos)
        print('processos_novos: ', len(processos_novos))
        Processo.insert_batch(base, processos_novos)

    def gera_relatorio_cadastro(self, base, tipo_data, update_existente=False, dias_antes=7, dias_depois=7):
        self.driver.get(self.pagina_busca)
        self.driver.find_element_by_id('fPesquisa:lblBtMudarFiltro').click()
        try_click(self.driver, 'fPesquisa:_idJsp228', tipo='ID')

        # SELECIONA A OPÇÃO CADASTRAMENTO
        aguarda_presenca_elemento(self.driver, "fPesquisa:datas", tipo="ID", aguarda_visibilidade=True)
        opcoes = Select(self.driver.find_element_by_id('fPesquisa:datas'))
        opcoes.select_by_visible_text(tipo_data)

        # PREENCHE O CAMPO DE DATA
        intervalo_de_datas = self.formata_datas(dias_antes, dias_depois)

        aguarda_presenca_elemento(self.driver,  "fPesquisa:dataInicial", tipo="ID", aguarda_visibilidade=True)
        self.preenche_campo(intervalo_de_datas[0], "fPesquisa:dataInicial", tipo="ID", limpar_string=False)
        self.preenche_campo(intervalo_de_datas[1], "fPesquisa:dataFinal", tipo="ID", limpar_string=False)
        # FIM DO PREENCHIMENTO DE DATAS

        # CLICA NO BOTÃO DE PESQUISAR
        self.driver.find_element_by_id('fPesquisa:_idJsp224').click()
        self.driver.execute_script("window.scrollTo(0,100)")

        msg_erro = self.driver.find_element_by_id('subviewMessages:formHeader:msgErro')
        if msg_erro and msg_erro.is_displayed():
            if msg_erro.text.find('não encontrou nenhum Processo') > -1:
                return

        # CLICA NO BOTÃO DE EXPORTAR EXCEL
        aguarda_presenca_elemento(self.driver, "fPesquisa:_idJsp245", tipo='ID', aguarda_visibilidade=True)
        self.driver.find_element_by_id('fPesquisa:_idJsp245').click()
        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        xpath = '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[9]/option'
        aguarda_presenca_elemento(self.driver, xpath, aguarda_visibilidade=True)
        self.driver.find_element_by_xpath(xpath).click()
        caminho_arquivo = self.baixa_planilha()
        df = pd.read_excel(caminho_arquivo)
        # df = pd.read_excel('C:\downloads\swap\bec\cliente\temp\6ca90ed4-8093-11ec-b252-5ccd5b383370\temp-1643413137542.xls')
        df = df.astype(str)
        df.fillna('')

        dados_planilha = []
        sequenciais = []
        for index, row in df.iterrows():
            sequencial = row['PROCESSO SEQ Nº'].strip()
            sequenciais.append(sequencial)
            prc_autor = self.trata_nomes(row['NOME AUTOR'], 80) if row['NOME AUTOR'] != 'nan' else None
            prc_comarca = self.trata_nomes(row['COMARCA'], 45) if row['COMARCA'] != 'nan' else None
            prc_numero = row['PROCESSO 1ª INSTANCIA Nº'].strip()
            carteira = self.verifica_carteira(sequencial)
            estado = tratar_estado(row['ESTADO'])
            area = 2 if row['DIVISAO RESPONSAVEL'] == 'NACIONAL TRABALHISTA' else 1
            cadastro = row['DATA CADASTRO']
            prc_situacao = row['SITUAÇÃO'].strip() if row['SITUAÇÃO'] != 'nan' else None
            prc_objeto1 = row['OBJETO ACAO'].strip() if row['OBJETO ACAO'] != 'nan' else None
            prc_objeto2 = row['ESP OBJETO ACAO'].strip() if row['ESP OBJETO ACAO'] != 'nan' else None
            prc_objeto3 = row['DET ESP OBJETO ACAO'].strip() if row['DET ESP OBJETO ACAO'] != 'nan' else None

            if cadastro is not None:
                cadastro = datetime.strptime(cadastro, '%d/%m/%Y %H:%M')

            prc = {'prc_sequencial': sequencial, 'prc_numero': prc_numero, 'prc_autor': prc_autor,
                   'prc_numero_processum': prc_numero, 'prc_carteira': carteira, 'prc_estado': estado,
                   'prc_comarca': prc_comarca, 'prc_objeto1': prc_objeto1, 'prc_objeto2': prc_objeto2,
                   'prc_objeto3': prc_objeto3, 'prc_data_cadastro': cadastro, 'prc_data': cadastro,
                   'prc_area': area, 'prc_situacao': prc_situacao}

            dados_planilha.append(prc)

            if tipo_data == 'Data Log Citação':
                # citacao = row['DATA CITACAO']
                # prc['ctg_data_citacao'] = datetime.strptime(citacao, '%d/%m/%Y %H:%M')
                prc['ctg_data_citacao'] = datetime.strptime(intervalo_de_datas[0], '%d/%m/%Y')
                self.processos_contingencia.append(prc)

        os.remove(caminho_arquivo)

        procs_base = Processo.get_processos_by_sequencial(base, sequenciais)
        sequenciais_base = {}
        for p in procs_base:
            sequenciais_base[p['prc_sequencial']] = p

        processos_novos = []
        processos_existentes = []
        # SEPARA OS PROCESSOS QUE NÃO ESTÃO NA BASE
        for obj in dados_planilha:
            if obj['prc_sequencial'] not in sequenciais_base:
                self.processos_novos.append(obj)
                processos_novos.append(obj)
            else:
                # obj['prc_id'] = sequenciais_base[obj['prc_sequencial']]['prc_id']
                # processos_existentes.append(obj)
                processos_existentes.append(sequenciais_base[obj['prc_sequencial']]['prc_id'])

        processos_novos = self.check_proc_dup(processos_novos)
        print('processos_novos: ', len(processos_novos))
        print('processos_existentes', len(processos_existentes))
        Processo.insert_batch(base, processos_novos)

        if update_existente and len(processos_existentes) > 0:
            print('Iniciando update')
            Processo.update_batch(base, processos_existentes, {'prc_data_update1': None})
            print('Fim do update')

    # VERFICA QUAL É A CARTEIRA, E RETORNA O VALOR ADEQUADO
    def verifica_carteira(self, sequencial):
        A = str(sequencial)
        aux_seq = ''
        tam = len(A)
        tam -= 1
        cont = 0
        while tam > 0 and cont < 2:
            B = A[tam]
            aux_seq = B + aux_seq
            if B == '-':
                cont += 1
            tam -= 1

        if aux_seq == '--148':
            return 2
        return 1

    # FAZ O TRATAMENTO NA PARTE ATIVA, PARA EVITAR NUMEROS GRANDES
    def trata_nomes(self, nome, tamanho=100):
        if nome is None or len(nome) <= tamanho:
            return nome

        nome = nome.replace("'", " ")
        if len(nome) <= tamanho:
            return nome

        x = nome.split("REPRESENTADO")
        aux_nome = x[0]
        if len(aux_nome) <= tamanho:
            return aux_nome

        x = aux_nome.split(",")
        aux_nome = x[0]
        if len(aux_nome) <= tamanho:
            return aux_nome

        return corta_string(aux_nome)

    # FAZ O TRATAMENTO NA PARTE ATIVA, PARA EVITAR NUMEROS GRANDES
    def trata_parte_ativa(self, parte_ativa):
        if parte_ativa is None:
            return parte_ativa
        aux_ativa = ''
        tam = len(parte_ativa)
        for i in range(tam):
            if parte_ativa[i] == ',':
                break
            aux_ativa += parte_ativa[i]
        aux_ativa = aux_ativa.replace("'", " ")

        if "REPRESENTADO" in aux_ativa:
            x = aux_ativa.split("REPRESENTADO")
            aux_ativa = x[0]

        return aux_ativa

    def check_proc_dup(self, procs):
        seqs = []
        n_procs = []
        for proc in procs:
            if proc['prc_sequencial'] in seqs:
                continue

            n_procs.append(proc)
            seqs.append(proc['prc_sequencial'])

        return n_procs
