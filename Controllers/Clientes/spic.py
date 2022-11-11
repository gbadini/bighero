from Controllers.Clientes._cliente import *
import json
import zipfile
import os
import fitz
import tabula
import pandas as pd
from Models.spicModel import *
from shutil import copy



# CLASSE DA VARREDURA DO PROCESSUM. HERDA OS METODOS DA CLASSE PROCESSUM
class SPICCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 2
        self.driver = False
        self.reiniciar_navegador = False
        self.file_to_ignore = False

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha):

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)

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
                query_and = query_and + " pra_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='SPIC')

            for proc in procs:
                try:
                    print('proc', proc)
                    filenameList = []
                    isEmpty = False
                    pasta_uid = str(uuid.uuid1())

                    temp_url = 'C:\\downloads\\temp\\'+db+'\\'+proc['prc_estado']+'\\'+str(proc['prc_id'])+'\\1\\'+pasta_uid+'\\'+str(proc['pra_id'])
                    create_folder(temp_url)
                    try:
                        copy(url_arquivos+'\\'+db+'\\'+proc['prc_estado']+'\\'+str(proc['prc_id'])+'\\1\\'+proc['pra_arquivo'], temp_url+'\\'+proc['pra_arquivo'])
                    except:
                        raise FatalException("Arquivo não localizado", proc['prc_estado'], self.plataforma, proc['prc_id'])

                    while isEmpty == False:
                        filenameList = []
                        for filename in os.listdir(temp_url):
                            print(temp_url+'\\'+filename)
                            filenameList = self.unzip_files(filename, filenameList, temp_url, temp_url, proc)

                        for filename in os.listdir(temp_url):
                            print(filename)
                            print(filename.endswith(".zip"))
                            if filename.endswith(".zip"):
                                print('entrei')
                                filenameList = [1]
                                break

                        print('filenameList',filenameList)
                        if not filenameList:
                            isEmpty = True

                    spics_base = Spic.select(self.conn[db], proc['prc_id'])
                    spc_base = {}
                    tabela_localizada = False
                    for spc in spics_base:
                        spc_base[spc['spc_numero']] = {'data_min': spc['spc_data_min'],
                                                       'data_max': spc['spc_data_max'],
                                                       'voz': spc['spc_voz'],
                                                       'sms': spc['spc_sms'],
                                                       'duracao': spc['spc_tempo'],
                                                       'spc_id': spc['spc_id'],
                                                       }

                    self.check_folders(temp_url, temp_url)

                    dados = []
                    numeros = {}
                    tableList = []
                    for pfdFile in os.listdir(temp_url):
                        print('varrendo', pfdFile)
                        if pfdFile.endswith(".xlsx") or pfdFile.endswith(".xls"):
                            print('não é pdf')
                            pp = pfdFile.rfind('.')
                            if os.path.isfile(temp_url + '\\' + pfdFile[0:pp] + '.pdf'):
                                continue
                            tableList = pd.read_excel(temp_url + '\\' + pfdFile)
                            # tableList = tabula.read_pdf(temp_url + '\\' + pfdFile, pages='all')

                        if pfdFile.endswith(".pdf"):
                            try:
                                reader = fitz.open(temp_url+'\\'+pfdFile)
                            except:
                                self.file_to_ignore = proc['pra_id']
                                raise FatalException("Arquivo pdf com problema", proc['prc_estado'], self.plataforma, proc['prc_id'])

                            total_pages = reader.pageCount
                            # print('total_pages', total_pages)
                            del reader

                            len_ciclo = 250
                            ciclos = math.ceil(total_pages/len_ciclo)
                            tableList = []
                            for i in range(1, ciclos+1):
                                pgmax = total_pages if i == ciclos else i*len_ciclo
                                pgmin = (i*len_ciclo)-(len_ciclo-1)
                                # print(pgmin, pgmax)
                                try:
                                    tableList += tabula.read_pdf(temp_url+'\\'+pfdFile, pages=str(pgmin)+'-'+str(pgmax))
                                except:
                                    pass

                        print(temp_url+'\\'+pfdFile)
                        # print(tableList[0].dtypes)
                        # print(tableList[0].head())
                        for table in tableList:
                            campo_chamador, campo_chamado, campo_duracao = self.find_fields(table)
                            if not campo_duracao:
                                continue

                            tabela_localizada = True
                            table[campo_chamador] = table[campo_chamador].astype(str)
                            table[campo_chamado] = table[campo_chamado].astype(str)
                            table[campo_duracao] = table[campo_duracao].astype(str)
                            if 'Status' not in table:
                                continue
                            table['Status'] = table['Status'].astype(str)

                            for i in range(0, len(table)):
                                chamador = self.format_string(table[campo_chamador][i])
                                chamado = self.format_string(table[campo_chamado][i])

                                if chamador == 'nan' or len(chamado) < 8 or len(chamado) > 15:
                                    continue

                                if self.find_prob_numbers(chamado):
                                    continue

                                if (table['Status'][i].find('Complet') > -1 or table['Status'][i].find('Entreg') > -1):
                                    if chamado in spc_base and chamado not in numeros:
                                        numeros[chamado] = spc_base[chamado]
                                    campo_data = self.format_string(table['Data'][i])
                                    campo_hora = self.format_string(table['Hora'][i])
                                    dia = datetime.strptime(campo_data + ' ' + campo_hora, '%d/%m/%Y %H:%M:%S')
                                    voz, sms, duracao = self.check_tipo(table, i, campo_duracao)
                                    if voz == 1 and duracao < 5:
                                        continue
                                    # duracao = self.format_string(table[campo_duracao][i])
                                    # duracao = int(duracao) if table['Tra'][i] == 'Voz' else 0
                                    if chamado not in numeros:
                                        # voz = 1 if table['Tra'][i] == 'Voz' else 0
                                        # sms = 1 if table['Tra'][i] == 'SMS' else 0
                                        # duracao = int(table[campo_duracao][i]) if table['Tra'][i] == 'Voz' else 0
                                        numeros[chamado] = {'data_min': dia,
                                                                        'data_max': dia,
                                                                        'voz': voz,
                                                                        'sms': sms,
                                                                        'duracao': duracao,
                                                                        'spc_id': None
                                                                        }
                                    else:
                                        if numeros[chamado]['spc_id'] is not None:
                                            if dia <= numeros[chamado]['data_max'] and dia >= numeros[chamado]['data_min']:
                                                continue

                                        numeros[chamado]['voz'] += voz
                                        numeros[chamado]['sms'] += sms
                                        numeros[chamado]['duracao'] += duracao

                                        # if table['Tra'][i] == 'Voz':
                                        #     numeros[chamado]['voz'] += 1
                                        #     # duracao = table[campo_duracao][i].replace('\r', '').replace('E210','')
                                        #     numeros[chamado]['duracao'] += int(duracao)
                                        # if table['Tra'][i] == 'SMS':
                                        #     numeros[chamado]['sms'] += 1

                                        if dia < numeros[chamado]['data_min']:
                                            numeros[chamado]['data_min'] = dia

                                        if dia > numeros[chamado]['data_max']:
                                            numeros[chamado]['data_max'] = dia

                    for n in numeros:
                        if int(numeros[n]['voz']) == 0 and int(numeros[n]['sms']) == 0:
                            continue

                        if int(numeros[n]['duracao']) < 5 and int(numeros[n]['sms']) == 0:
                            continue

                        dados.append({'spc_numero': n,
                                      'spc_id': numeros[n]['spc_id'],
                                      'spc_prc_id': proc['prc_id'],
                                      'spc_data_min': numeros[n]['data_min'],
                                      'spc_data_max': numeros[n]['data_max'],
                                      'spc_voz': int(numeros[n]['voz']),
                                      'spc_sms': int(numeros[n]['sms']),
                                      'spc_tempo': int(numeros[n]['duracao'])})

                    # APAGA PASTA TEMPORÁRIA E TODOS OS ARQUIVOS
                    shutil.rmtree(temp_url)

                    if len(dados) == 0:
                        print('achei', temp_url+'\\'+pfdFile)
                        print('')
                        if len(spc_base) == 0 and len(tableList) != 0 and proc['pra_descricao'].upper().find('SPIC') == -1 and not tabela_localizada:
                            ProcessoArquivo.update(self.conn[db], [{'pra_id': proc['pra_id'], 'pra_tentativas': 12, }, ])
                            raise FatalException("Nenhum spic localizado", proc['prc_estado'], self.plataforma, proc['prc_id'])

                    for d in dados:
                        print(d)

                    if len(dados) > 0:
                        Spic.insert(self.conn[db], dados)
                    ProcessoArquivo.update(self.conn[db], [{'pra_id': proc['pra_id'],'pra_ocorrencia':len(dados) > 0,},])

                except MildException:
                    tb = traceback.format_exc()
                    self.logger.warning(tb, extra={'log_prc_id': proc['prc_id']})
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': proc['prc_id']})
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': proc['prc_id']})
                    ignorar_id.append(str(proc['pra_id']))

                    if self.file_to_ignore:
                        ProcessoArquivo.update(self.conn[db], [{'pra_id': self.file_to_ignore, 'pra_tentativas': 12, }, ])
                    self.file_to_ignore = False
                    continue

        return True

    def find_fields(self, table):
        if 'Chamado' in table:
            campo_chamado = 'Chamado'
            campo_chamador = 'Chamador'
        elif 'Assinante A' in table:
            campo_chamado = 'Assinante B'
            campo_chamador = 'Assinante A'
        else:
            return False, False, False

        campo_duracao = False
        for c in ('Durac', 'Dura\rc', 'Dur\rac', 'Du\rrac', 'D\rurac', 'Duração',):
            if c in table:
                campo_duracao = c
                break

        return campo_chamador, campo_chamado, campo_duracao

    def format_string(self, txt):
        return txt.replace('\r', '').replace('E210', '').replace('E410', '').replace('DD55', '').replace('.0', '')

    def find_prob_numbers(self, numero):
        probNumbers = ['0800', '8000', '4002', '4004', '3003', '3004',]
        probNumbers0 = ['080','800',]
        probNumbersQ = ['30033030','40044828','40043535','0800101515','6232168000','6232698800']
        for prob in probNumbers:
            if numero.find(prob) > -1 and numero.find(prob) < 4:
                return True

        for prob in probNumbers0:
            if numero.find(prob) == 0:
                return True

        for prob in probNumbersQ:
            if numero.find(prob) > -1:
                return True

        return False

    def check_tipo(self, table, i, campo_duracao):
        voz = 0
        sms = 0
        duracao = 0
        if 'Tra' in table:
            voz = 1 if table['Tra'][i] == 'Voz' else 0
            sms = 1 if table['Tra'][i] == 'SMS' or table['Tra'][i] == 'TORP.' or table['Tra'][i] == 'TOR\rP.' else 0
            duracao = self.format_string(table[campo_duracao][i])
            duracao = int(duracao) if voz == 1 else 0

        else:
            duracao = self.format_string(table[campo_duracao][i])
            if duracao == '00:00:00':
                voz, sms = 0, 1
                duracao = 0
            else:
                voz, sms = 1, 0
                h = int(duracao[0:2]) * 3600
                m = int(duracao[3:5]) * 60
                s = int(duracao[6:8])
                duracao = h + m + s


        return voz, sms, duracao
    
    
    def unzip_files(self, filename, filenameList, temp_url, target, proc):
        size = os.path.getsize(temp_url+'\\'+filename)
        if size == 0:
            return []

        if os.path.isdir(temp_url+'\\'+filename):
            for subfilename in os.listdir(temp_url + '\\' + filename):
                filenameList = self.unzip_files(subfilename, filenameList, temp_url+'\\'+filename, target, proc)
        elif filename.endswith(".zip") and (filename not in filenameList):
            # filenameList.append(filename)
            try:
                with zipfile.ZipFile(temp_url + '\\' + filename, "r") as zip_ref:
                    zip_ref.extractall(target)
                if os.path.exists(temp_url + '\\' + filename):
                    os.remove(temp_url + '\\' + filename)
                else:
                    print("O arquivo nao existe")
            except:
                self.file_to_ignore = proc['pra_id']
                raise FatalException("Arquivo pdf com problema", proc['prc_estado'], self.plataforma, proc['prc_id'])

        elif filename.endswith(".zip") and (filename in filenameList):
            print(temp_url+'\\'+filename)
            filenameList.remove(filename)
            if os.path.exists(temp_url + '\\' + filename):
                os.remove(temp_url + '\\' + filename)
            else:
                print("O arquivo nao existe")

        return filenameList

    def check_folders(self, temp_url, target):
        for filename in os.listdir(temp_url):
            if os.path.isdir(temp_url + '\\' + filename):
                self.check_folders(temp_url + '\\' + filename, target)
            elif temp_url != target:
                shutil.move(temp_url + '\\' + filename, target + '\\' + filename)