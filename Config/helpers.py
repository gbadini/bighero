from selenium import webdriver
import tkinter as tk
from Views.form import MainApplication
from selenium.common.exceptions import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from datetime import datetime, timedelta
from Config.customMethods import *
from pywinauto.application import Application
from pywinauto.keyboard import SendKeys
from pywinauto.findwindows import *
import time, re, os, uuid, shutil, cgi, html
import csv
from unidecode import unidecode
import unicodedata
import traceback
from xhtml2pdf import pisa

parametros = {}
plataformas = {2:'pje', 3:'projudi', 4:'fisico', 5:'esaj', 6:'tucujuris', 7:'eproc', 9:'ppe'}
# , 12:'pda', 13:'sigweb
plataformas_cliente = {1:'processum', 11:'espaider', 8:'tedesco',}
carteira = {1:'1,2', 11:'5'}

estados = {
    'bec': ('AC', 'AM', 'AP', 'CE', 'DF', 'GO', 'MA', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'RN', 'RO', 'RR', 'TO',
            'TRT01','TRT02','TRT03','TRT04','TRT05','TRT06','TRT07','TRT08','TRT09','TRT10','TRT11','TRT12','TRT13','TRT14',
            'TRT15','TRT16','TRT17','TRT18','TRT19','TRT20','TRT21','TRT22','TRT23','TRT24','TRF01','TRF02','TRF03','TRF04','TRF05'),
    'ede': ('BA','TRT05','TRF01'),
    'rek': ('AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
            'TRT01','TRT02','TRT03','TRT04','TRT05','TRT06','TRT07','TRT08','TRT09','TRT10','TRT11','TRT12','TRT13','TRT14',
            'TRT15','TRT16','TRT17','TRT18','TRT19','TRT20','TRT21','TRT22','TRT23','TRT24','TRF01','TRF02','TRF03','TRF04','TRF05'),
    'hasson': ('PR',),
}

pagamento = {
    'bec': {'peticao': True},
    'rek': {'peticao': False},
    'ede': {'peticao': False},
    'hasson': {'peticao': False},
}

esp_agenda = {
    'bec': (),
    'rek': (),
    'ede': ('Juntada de AR - Aviso','Conclusos para Despacho','Conclusos para Decisão','Conclusos para Sentença','Conclusos para Sentença Extintiva','Conclusos para Pedido Urgência','Conclusos para Análise de Recurso','Conclusos para Homologação','Conclusos para Autos Retornados das Turmas Recursais','Decorrido prazo de','Juntada de Conclusão','Conclusos para Relatório Voto Ementa','Juntada de Petição de Contrarrazões Recursais','Juntada de Requerimento de Pedido de Sustentacão Oral','Intimação lido(a)','Distribuído por Sorteio','Remetidos os Autos para Turmas Recursais','Juntada de Petição de %','Recurso Autuado','Alteração de Tipo Conclusão','Juntada de Requerimento de Pedido de Preferência','Pedido de inclusão em pauta','CONCLUSOS PARA JULGAMENTO','CONCLUSOS PARA DESPACHO','JUNTADA DE TERMO','JUNTADA DE PETIÇÃO DE RÉPLICA','JUNTADA DE AVISO DE RECEBIMENTO','JUNTADA DE ATA DA AUDIÊNCIA','JUNTADA DE PETIÇÃO DE PROCURAÇÃO','JUNTADA DE PETIÇÃO DE CONTESTAÇÃO','JUNTADA DE ALVARÁ JUDICIAL','JUNTADA DE CARTA','JUNTADA DE ATO ORDINATÓRIO','JUNTADA DE CERTIDÃO','DISTRIBUÍDO POR SORTEIO','Juntada de Petição de Contestação','Conclusos para Sentença Extintiva','Ato ordinatório praticado','Documento analisado','Juntada de Petição de Petição','Remetidos os Autos para Secretaria','Alteração de Tipo Conclusão','Conclusos para Sentença','Conclusos para Despacho','Juntada de Petição de Requisição de Habilitação','Juntada de Petição de Outros Tipos de Petição','Expedida carta','Expedido ato ordinatório','Concluso para despacho','Juntada de Petição','Juntada de documento','Expedido alvará',),
    'hasson': (),
}

config_atas = {
    'bec': {'nome': 'ADVOCACIA MACIEL',},
    'rek': {'nome': 'RAMOS & KRUEL',},
    'ede': {'nome': 'EDE - ESCRITÓRIO DE DIREITO ECONOMICO ITANA BADARO',},
    'hasson': {'nome': 'HASSON ADVOGADOS',},
}

meses = {'janeiro': 1, 'fevereiro':2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,'julho': 7,'agosto': 8,'setembro': 9,'outubro': 10,'novembro': 11,'dezembro': 12, 'jan': 1, 'fev':2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,'jul': 7,'ago': 8,'set': 9,'out': 10,'nov': 11,'dez': 12, 'feb':2, 'apr': 4, 'may': 5, 'aug': 8, 'sep': 9,'oct': 10,'dec': 12}
trts = {'01': ["RJ"], '02':  ["SP"], '03': ["MG"], '04': ["RS"], '05': ["BA"], '06': ["PE"], '07': ["CE"], '08': ["AP", "PA"], '09': ["PR"], '10': ["DF", "TO"],
                '11': ["AM", "RR"], '12': ["SC"], '13': ["PB"], '14': ["AC", "RO"], '15': ["SP"], '16': ["MA"], '17': ["ES"], '18': ["GO"], '19': ["AL"], '20': ["SE"],
                 '21': ["RN"], '22': ["PI"], '23': ["MT"], '24': ["MS"]}
trfs = {'01': ["DF","AC","AP","AM","BA","GO","MA","MT","MG","PA","PI","RO","RR","TO",], '02': ["RJ","ES",], '03': ["SP","MS",], '04': ["PR","RS","SC",], '05': ["AL","CE","PB","PE","RN","SE",],}


dados_audiencia = {'tipo': ('Tipo da Audiência: Una','Audiência Una','Audiencia Una', 'Mero expediente', 'INSTRUÇÃO E JULGAMENTO','Conciliação,Instrução e Julgamento', 'CONCILIAÇÃO, INSTRUÇÃO E JULGAMENTO', 'Instrução', 'Conciliação', 'Mediação', 'Custódia', 'INST E JULGAMENTO', 'CEJUSC', 'Julgamento', 'Justificação', 'Preliminar', 'Inquirição', 'Perícia','Importação de Arquivos Multimídia','Importação Arquivos Multimídia','VLM','CONCILIATÓRIA','Comum','INQUIRITÓRIA','AUDIENCIA DO ART. 334','Recurso','Sessão de 2º Grau','DEPOIMENTO','SESSÃO VOLUNTÁRIA','Audiência','Audiencia',),
                   'status': ('Redesignada', 'CONVERTIDA EM DILIGENCIA', 'CONVERTIDA EM DILIGÊNCIA', 'Convertida', 'realizada com Despacho', 'Realizada', 'Negativa', 'Designada', 'Marcada', 'Cancelada', 'Antecipada', 'Adiada', 'Sem Acordo', 'Retificação', 'Pendente', 'Suspensa','Agendada','Prorrogada', 'Intimado','NÃO INFORMADA','INFRUTÍFERA')}

capitais = {'RO': 'Porto Velho', 'AM': 'Manaus', 'AC': 'Rio Branco', 'MS': 'Campo Grande', 'AP': 'Macapá', 'DF': 'Brasília', 'RR': 'Boa Vista', 'MT': 'Cuiabá', 'TO': 'Palmas', 'SP': 'São Paulo', 'PI': 'Teresina', 'RJ': 'Rio de Janeiro', 'PA': 'Belém', 'GO': 'Goiânia', 'BA': 'Salvador', 'SC': 'Florianópolis', 'MA': 'São Luís', 'AL': 'Maceió', 'RS': 'Porto Alegre', 'PR': 'Curitiba', 'MG': 'Belo Horizonte', 'CE': 'Fortaleza', 'PE': 'Recife', 'PB': 'João Pessoa', 'SE': 'Aracaju', 'RN': 'Natal', 'ES': 'Vitória'}
cidades = {
    'SC': {'Federal de Santa Catarina': 'Florianópolis', 'Florianópolis': 'Florianópolis', 'Juízo do juizado especial cível e criminal e de violência doméstica e familiar contra a mulher': 'Itajaí'},
    'RO': {'Porto Velho': 'Porto Velho',},
    'AM': {'Manaus': 'Manaus',},
    'AC': {'Rio Branco': 'Rio Branco',},
    'MS': {'Campo Grande': 'Campo Grande',},
    'MA': {'Juizado Especial Cível e das Relações de Consumo': 'São Luís', 'Juizado Cível E Das Relações De Consumo': 'São Luís','º Juizado Especial Cível das Relações de Consumo': 'São Luís',},
    'AP': {'Macapá': 'Macapá',},
    'RR': {'Boa Vista': 'Boa Vista',},
    'MT': {'Cuiabá': 'Cuiabá', 'Campo novo dos parecis':'Campo novo dos parecis','Sto antônio do leverger': 'Santo antônio do leverger'},
    'TO': {'Palmas': 'Palmas', },
    'PI': {'Teresina': 'Teresina', 'São Rdo Nonato': 'São Raimundo Nonato', 'Piripiri': 'Piripiri'},
    'RJ': {'Rio de Janeiro': 'Rio de Janeiro', },
    'PA': {'Belém': 'Belém', 'Cejusc procon': 'Belém','ª Vara do Juizado Especial Cível': 'Belém',},
    'BA': {'Salvador': 'Salvador', 'vsje': 'Salvador', 'FSJE': 'Salvador', 'REGIÃO METROPOLITANA': 'Salvador', 'sto antônio de jesus': 'Santo Antônio de Jesus','Vit. da conquista':'Vitória da Conquista', 'Itabuna': 'Itabuna'},
    'AL': {'Maceió': 'Maceió', },
    'RS': {'Porto Alegre': 'Porto Alegre', },
    'PR': {'Curitiba': 'Curitiba',},
    'MG': {'Belo Horizonte': 'Belo Horizonte','ª UNIDADE JURISDICIONAL CÍVEL': 'Belo Horizonte'},
    'CE': {'Fortaleza': 'Fortaleza', 'unidade do juizado especial cível': 'Fortaleza', 'º juizado especial cível e criminal': 'Fortaleza', 'são gonçalo do amarante': 'São Gonçalo do Amarante'},
    'PE': {'Recife': 'Recife', 'Gabinete Do Des': 'Recife'},
    'PB': {'João Pessoa': 'João Pessoa','Centro administrativo integrado francisco de oliveira braga':'Conceição'},
    'SE': {'Aracaju': 'Aracaju',},
    'RN': {'Natal': 'Natal',},
    'ES': {'Vitória': 'Vitória'},
    'SP': {'Foro central juizados especiais cíveis': 'São Paulo','Foro central cível':'São Paulo'}
}
tipos_pje = ('DEFERIDO','EXPEDIDO ALVARÁ','DECORRIDO PRAZO','CANCELADA','RETORNO','ENTREGA','EXTINTA A PUNIBILIDADE','EXPEDIDA/CERTIFICADA','QUEBRA DE SIGILO BANCÁRIO','CONFIRMADA','JULGADA PROCEDENTE','JULGADA IMPROCEDENTE','JULGADA PARCIALMENTE PROCEDENTE','EMISSÃO DE CUSTA','PEDIDO CONHECIDO EM PARTE','ALTERAÇÃO','RECEBIDA A EMENDA','AGUARDANDO','VINCULAÇÃO','AGUARD. CUMPRIMENTO','EXCLUSÃO','DECLARADA','AO JUIZO','REDISTRIBUIÇÃO','DISTRIBUIÇÃO','JUNTAR','BAIXA','CONFLITO','OUTROS','AUDIÊNCIA','CADASTRO','CERTIDÃO','CERTIDAO','SUSPENSO','REMESSA','APENSADO','EXPEDIR OFICIO','AO GABINETE','ACOLHIDA','INDISPONIBILIDADE','REIMPRESSÃO','REJEITADA','OUTRAS DECISÕES','EFEITO SUSPENSIVO','RECURSO','IMPEDIMENTO','SUSPEIÇÃO','RETIFICAÇÃO','ASSISTÊNCIA JUDICIÁRIA GRATUITA','INDEFERIDA','ATO ORDINATÓRIO','EXTINTA A EXECUÇÃO','DETERMINADO','ENVIADO','DETERMINADA REQUISIÇÃO','EVENTO PROJUDI','CONTA ATUALIZADA','PROFERIDA SENTENÇA','MIGRADO','MEDIDA LIMINAR','BLOQUEIO/PENHORA','RETIFICADO','EXTINTO','DESENTRANHAMENTO','CONVERTIDO','EMBARGOS DE DECLARAÇÃO','MANDADO DEVOLVIDO','PROCESSO SUSPENSO','RECEBIDO','SUSPENSÃO','JUNTADA','ALTERADA','EXPEDIÇÃO','ANTECIPAÇÃO','CONCLUSOS','AUDIÊNCIA','REDISTRIBUÍDO','DISTRIBUÍDO','HOMOLOGADO','HOMOLOGADA','INCOMPETÊNCIA','RECEBIDOS OS AUTOS','REMETIDOS OS AUTOS','PUBLICADO','TRANSITADO EM JULGADO','JULGADO','DECISÃO','DESARQUIVADO','CUMPRIMENTO DE SENTENÇA','ARQUIVADO','ARQUIVAMENTO','DESPACHO','CÁLCULO','DISPONIBILIZADO');

# ABRE O NAVEGADOR E CRIA O WEBDRIVER
def create_browser_instance(caminho_download, headless=False, wait_loading=True, browser='Chrome'):
    '''
    :param str caminho_download: local de destino dos downloads realizados
    :param bool headless: O navagador será executado de maneira headless(invisível para o usuário)? - Utilizar como False se precisar realizar downloads
    '''
    import json

    if browser == 'IE':
        return webdriver.Ie('C:\\PycharmProjects\\diario\\IEDriverServer.exe')

    settings = {"recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
                "selectedDestinationId": "Save as PDF", "version": 2,
                'download_restrictions': 0,
                }

    chrome_options = webdriver.ChromeOptions()

    prefs = {'plugins.always_open_pdf_externally': True,
             'plugins.plugins_disabled': False,
             "download.directory_upgrade": True,
             "download.prompt_for_download": False,
             # "profile.default_content_settings.popups": 0,
             # 'safebrowsing.disable_download_protection': True,
             # "profile.default_content_setting_values.automatic_downloads": 1,
             'download.default_directory': caminho_download,
             'savefile.default_directory': caminho_download,
             'safebrowsing.enabled': True,
             'download_restrictions': 0,
             'download.download_restrictions': 0,
             # 'download.extensions_to_open': "msg",
             'printing.print_preview_sticky_settings.appState': json.dumps(settings),

            # "printing.default_destination_selection_rules": {
            #     "kind": "local",
            #     "namePattern": "Save as PDF",
            # },
             }

    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('ignore-certificate-errors')
    chrome_options.add_argument("window-size=1300,900")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--safebrowsing-disable-download-protection")
    chrome_options.add_argument("safebrowsing-disable-extension-blacklist")
    chrome_options.add_argument('--safebrowsing-manual-download-blacklist')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    if headless:
        chrome_options.add_argument("--headless")

    chromedriver_path = get_full_path('chromedriver.exe')
    if not wait_loading:
        capabilities = DesiredCapabilities.CHROME
        capabilities["pageLoadStrategy"] = "none"
        driver = Chrome(chromedriver_path, options=chrome_options, desired_capabilities=capabilities)
    else:
        driver = Chrome(chromedriver_path, options=chrome_options)

    return driver

def get_full_path(folder=''):
    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir.joinpath(folder))

def get_escritorio_nome(db):
    config = config_atas[db]
    print(config)
    return config['nome']


def load_form():
    root = tk.Tk()
    mainform = MainApplication(root)
    mainform.pack(side="top", fill="both", expand=True)
    root.protocol("WM_DELETE_WINDOW", mainform.close)
    root.withdraw()
    try:
        root.mainloop()
    except:
        tb = traceback.format_exc(limit=1)
        if tb.find('KeyboardInterrupt') == -1:
            raise


# FOCA NA JANELA A PARTIR DO PID
def foca_janela(process_children):
    for child in process_children:
        # print(child.pid)
        app = Application()
        try:
            # print("select window")
            app.connect(process=child.pid, timeout=0.5)
            app_dialog = app.top_window()
            if str(app_dialog.element_info).find('Chrome') > -1:
                print('info',app_dialog.element_info)
                app_dialog.minimize()
                app_dialog.restore()
                app_dialog.move_window(x=0, y=0, width=1400, height=900, repaint=True)
                app_dialog.set_focus()
                return [child]

        except Exception as e:
            pass

    return process_children

# TENTA CLICAR NO ELEMENTO SEM GERAR ERRO
def try_click(driver, elemento, tipo='XPATH', tentativas=1, intervalo=1):
    '''
    :param WebDriver driver: webdriver do selenium
    :param str elemento: identificador do elemento a ser localizado
    :param str tipo: como o elemento será localizado (ID, XPATH, CLASSNAME, CSS, etc)
    '''
    for i in range(0, tentativas):
        by = getattr(By, tipo)
        try:
            driver.find_element(by, elemento).click()
        except:
            return False
        if tentativas > 1:
            time.sleep(intervalo)

    return True

# VERIFICA SE O ELEMENTO POSSUI O TEXTO ESPECIFICO
def check_text(driver, elemento, texto, tipo='XPATH', upper=True):
    '''
    :param WebDriver driver: webdriver do selenium
    :param str elemento: identificador do elemento a ser localizado
    :param str texto: texto a ser localizado
    :param str tipo: como o elemento será localizado (ID, XPATH, CLASSNAME, CSS, etc)
    :param bol upper: Os textos serão configurados como uppercase para ignorar diferenças de formatação
    '''
    by = getattr(By, tipo)
    try:
        txt_el = driver.find_element(by, elemento).text
        texto_elemento = txt_el.upper() if upper else txt_el
        texto = texto.upper() if upper else texto

        if texto_elemento.find(texto) > -1:
            return True

    except:
        return False

    return False

# VERIFICA SE O ELEMENTO POSSUI O TEXTO ESPECIFICO
def get_text(driver, elemento, tipo='XPATH', retorna_vazio=False, trim=True):
    '''
    :param WebDriver driver: webdriver do selenium
    :param str elemento: identificador do elemento a ser localizado
    :param str texto: texto a ser localizado
    :param str tipo: como o elemento será localizado (ID, XPATH, CLASSNAME, CSS, etc)
    :param bol retorna_vazio: Se deve retornar string vazia ao invés de False caso o elemento exista, mas esteja vazio
    '''
    by = getattr(By, tipo)
    try:
        txt_el = driver.find_element(by, elemento).text
        if trim:
            txt_el = txt_el.strip()
        if txt_el == '':
            if retorna_vazio:
                return ''

            return False

        return txt_el
    except:
        return False

#CONFERE VÁRIOS ELEMENTOS E RETORNA O QUE LOCALIZAR
def localiza_elementos(driver, elementos, tipo='XPATH', desconsidera_vazio=False, desconsidera_oculto=False, retorna_multiplos = False):
    for el in elementos:
        by = getattr(By, tipo)
        try:
            e = driver.find_element(by, el)
            if not desconsidera_vazio and not desconsidera_oculto:
                if retorna_multiplos:
                    return driver.find_elements(by, el)
                return e

            if desconsidera_vazio and e.text.strip() == '':
                continue

            if desconsidera_oculto and not e.is_displayed():
                continue

            if retorna_multiplos:
                return driver.find_elements(by, el)
            return e

        except:
            pass

    return False

# RETORNA CONFIGURAÇÃO DE PAGAMENTO DA BASE
def pagamento_base(db):
    '''
    :param str db: Noma da Base
    '''
    return pagamento[db]

# RETORNA CONFIGURAÇÃO DE AGENDA DA BASE
def agenda_base(db):
    '''
    :param str db: Noma da Base
    '''
    return esp_agenda[db]

# RETORNA OS ESTADOS DE CADA TRT
def trt_estado(trt):
    '''
    :param int id_plataforma: ID da plataforma
    '''
    r = re.search('(\\d+)', trt)
    nro = r.group(0)

    return trts[nro]

# RETORNA OS ESTADOS DE CADA TRT
def trf_estado(trt):
    '''
    :param int id_plataforma: ID da plataforma
    '''
    r = re.search('(\\d+)', trt)
    nro = r.group(0)

    return trfs[nro]

# RETORNA O NOME DA PLATAFORMA SELECIONADA
def nome_plataforma(id_plataforma, estado=False):
    '''
    :param int id_plataforma: ID da plataforma
    '''
    plts = plataformas
    if estado == '*':
        plts.update(plataformas_cliente)

    if id_plataforma not in plts:
        return ''

    return plts[id_plataforma]

# RETORNA O NOME DA PLATAFORMA SELECIONADA
def carteira_plataforma(id_plataforma):
    '''
    :param int id_plataforma: ID da plataforma
    '''
    return carteira[id_plataforma]

# RETORNA O ID DA PLATAFORMA SELECIONADA
def id_plataforma(nome_plataforma, cliente=False):
    '''
    :param str nome_plataforma: Nome da plataforma
    '''

    if nome_plataforma.upper() == 'TRT':
        return 2

    if cliente:
        for p in plataformas_cliente:
            if plataformas_cliente[p].upper() == nome_plataforma.upper():
                return p

    for p in plataformas:
        if plataformas[p].upper() == nome_plataforma.upper():
            return p

# AJUSTA O NUMERO CNJ PARA FAZER A VARREDURA
def ajusta_numero(numero, tratar_tamanhos=False):
    '''
    :param str numero: retorna a data e hora atual
    '''
    numero_original = numero
    numero = numero.replace(' ','').replace('-','').replace('.','').replace('\t','').replace('\t','').replace('\r','').replace('/','')
    numero = strip_html_tags(numero)
    numero = numero.lstrip("0")

    if tratar_tamanhos:
        if len(numero_original) <= 11:
            return numero.rjust(11, "0")

        if len(numero_original) <= 14 or (numero_original.find('/') > -1 and len(numero_original) <= 18):
            return numero.rjust(14, "0")

    numero = numero.rjust(20, "0")
    return numero

# LOCALIZA CNJ NA STRING
def localiza_cnj(texto, regex="(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|([0-9]{17,20})"):
    '''
    :param str numero: retorna a data e hora atual
    '''
    r = re.search(regex, texto)
    if r:
        return r.group(0)

    return False

# SUSPENDE A EXECUÇÃO DO SCRIPT ATÉ QUE O ELEMENTO ESTEJA PRESENTE (ALTERNATIVA AO METODO NATIVO "WAIT" DO SELENIUM QUE APRESENTA ERRO NA EXECUÇÃO)
def aguarda_presenca_elemento(driver, elemento, tempo=30, tipo='XPATH', latencia=0.2, aguarda_visibilidade=False):
    '''
    :param WebDriver driver: webdriver do selenium
    :param str elemento: identificador do elemento a ser localizado
    :param float tempo: segundos que o script aguardará a presença do elemnto
    :param str tipo: como o elemento será localizado (ID, XPATH, CLASSNAME, CSS, etc)
    :param bol latencia: tempo de espera entre cada checagem
    '''
    inicio = time.time()
    f = False
    by = getattr(By, tipo)
    while not f:
        try:
            f = len(driver.find_elements(by, elemento)) > 0
            time.sleep(latencia)
            tempoTotal = time.time() - inicio
            if tempoTotal >= tempo:
                return False
        except:
            pass

    if aguarda_visibilidade:
        wait = WebDriverWait(driver, tempo)
        try:
            wait.until(EC.visibility_of_element_located((by, elemento)))
        except:
            return False

    # O WAIT NATIVO DO SELENIUM APRESENTA ERRO DE CONEXÃO ABORTADA QDO EXECUTADO DUAS VEZES EM SEQUENCIA
    # wait = WebDriverWait(driver, tempo)
    # by = getattr(By, tipo)
    # try:
    #     wait.until(EC.presence_of_element_located((by, elemento)))
    # except TimeoutException:
    #     del wait
    #     return False
    #
    # del wait
    return True


# AGUARDA PRESENÇA DO ALERTA
def aguarda_alerta(driver, tempo=1, aceitar=True, rejeitar=True):
    try:
        wait = WebDriverWait(driver, tempo)
        wait.until(EC.alert_is_present())
        if aceitar:
            driver.switch_to.alert.accept()
        else:
            if rejeitar:
                driver.switch_to.alert.dismiss()
        return True
    except NoAlertPresentException:
        pass
    except TimeoutException:
        pass
    except UnexpectedAlertPresentException:
        if aceitar:
            driver.switch_to.alert.accept()
        else:
            if rejeitar:
                driver.switch_to.alert.dismiss()
        return True

    return False

# RETORNA AS BASES QUE POSSUEM PROCESSOS NO ESTADO INDICADO
def get_bases(uf):
    '''
    :param str uf: estado a ser localizado
    '''
    bases = []
    for e in estados:
        if uf in estados[e] or uf == '*':
            bases.append(e)

    return bases

# LOCALIZA PARÂMETROS ADICIONAIS PARA A QUERY DE CADA ESTADO/PLATAFORMA
def get_and(uf, plataforma, grau=1):
    '''
    :param str uf: estado a ser localizado
    :param int plataforma: plataforma a ser localizada
    '''
    ands = {}
    if grau == 2:
        ands['AM'] = {
            5: " ",
        }
    else:
        ands['AM'] = {
            5: " (prc_projudi = 0 or prc_projudi is null)",
            3: " (prc_esaj is null or prc_esaj=0)"
        }

    ands['BA'] = {
        2: " (prc_projudi = 0 or prc_projudi is null)",
        3: " (prc_pje = 0 or prc_pje is null) and (prc_esaj = 0 or prc_esaj is null)",
        4: " ((prc_pje = 0 and prc_esaj=0 and prc_projudi=0 and prc_fisico is null) or (prc_fisico=1 and (prc_segredo=0 or prc_segredo is null))) and (prc_numero LIKE '%805%' OR prc_numero LIKE '%8.05%')",
        5: " (prc_pje = 0 or prc_pje is null) and (prc_projudi = 0 or prc_projudi is null)"
    }
    ands['CE'] = {
        5: " (prc_pje = 0 or prc_pje is null)",
    }
    ands['DF'] = {
        4: " (prc_pje = 0)",
    }
    ands['ES'] = {
        3: " (prc_pje = 0 or prc_pje is null)",
        4: " (prc_pje = 0 or prc_pje is null) and (prc_projudi = 0 or prc_projudi is null)",
    }
    ands['MA'] = {
        2: " ",
        3: " (prc_pje is null or prc_pje=0) and (prc_fisico is null or prc_fisico=0) and (prc_projudi = 1 or prc_projudi is null)",
        4: " (prc_pje is null or prc_pje = 0) and (prc_projudi is null or prc_projudi=0)",
    }
    if grau == 2:
        ands['MG'] = {
            4: " "
        }
    else:
        ands['MG'] = {
            2: " (prc_projudi is null or prc_projudi=0) and (prc_fisico is null or prc_fisico=0)",
            3: " (prc_pje is null or prc_pje=0) and (prc_fisico is null or prc_fisico=0)",
            4: " (prc_pje is null or prc_pje=0) and (prc_projudi is null or prc_projudi=0) and (prc_fisico is null or prc_fisico=1)"
        }

    ands['MT'] = {
        2: " (prc_projudi is null or prc_projudi=0) ",
        3: " (prc_pje is null or prc_pje=0) "
    }
    ands['PA'] = {
        3: " prc_numero not like '08%' and (prc_pje is null or prc_pje = 0) and (prc_fisico is null or prc_fisico=0)",
        4: " (prc_pje is null or prc_pje = 0) and (prc_projudi is null or prc_projudi=0)",
    }
    ands['PB'] = {
        4: " (prc_pje = 0)",
    }
    ands['PE'] = {
        4: " (prc_pje = 0)",
    }
    ands['PI'] = {
        3: " (prc_pje = 0 or prc_pje is null)",
        4: " (prc_pje = 0) and (prc_projudi=0) and (prc_fisico = 1 or prc_fisico is null)",
    }
    ands['RJ'] = {
        9: " (prc_pje = 0 or prc_pje is null) and (prc_eproc = 0 or prc_eproc is null)",
    }
    ands['RN'] = {
        5: " (prc_pje = 0)",
        3: " (prc_pje = 0 and prc_esaj = 0)",
    }
    ands['RO'] = {
        4: " (prc_pje = 0)",
    }
    ands['RS'] = {
        9: " (prc_eproc = 0 or prc_eproc is null) and (prc_fisico = 0 or prc_fisico is null)",
        7: " (prc_ppe = 0 or prc_ppe is null or prc_eproc = 1 or prc_eproc is null) and (prc_fisico is null or prc_fisico = 0) "
    }
    ands['SC'] = {
        7: " (prc_esaj = 0 or prc_esaj is null or prc_migrado=1) and (prc_fisico = 0 or prc_fisico is null)",
        5: " (prc_eproc = 0 or prc_eproc is null) and (prc_fisico is null or prc_fisico = 0) "
    }

    if uf in ands:
        if plataforma in ands[uf]:
            if ands[uf][plataforma].strip() != '':
                return " and "+ands[uf][plataforma]

    return ""

# DETECTA A DATA EM UMA STRING
def localiza_data(dia_base, localiza_hora=False):
    dia_base = dia_base.strip()
    hora = ''
    if localiza_hora:
        r = re.findall("(\\d+)(\\:)(\\d+)", dia_base, re.IGNORECASE | re.DOTALL)
        if r:
            hora = ' '+r[0][0]+':'+r[0][2]
        else:
            r = re.findall("(\\d+)(h)(\\s+)|(\\d+)(h)(,)", dia_base, re.IGNORECASE | re.DOTALL)
            if r:
                hora = ' ' + r[0][3] + ':00'
            else:
                r = re.findall("(\\d+)(h)(\\d+)", dia_base, re.IGNORECASE | re.DOTALL)
                if r:
                    hora = ' ' + r[0][0]+':'+r[0][2]

    dia_base = dia_base.replace('.', '')
    r = re.findall("([0-9]{1,2})(\\s+)([a-zA-Z]{3})(\\s+)([0-9]{4})", dia_base, re.IGNORECASE | re.DOTALL)
    if r:
        ano = r[0][4]
        mes = r[0][2].lower()
        dia = r[0][0]

        if int(ano) < 1970 or int(ano) > 2090 or int(dia) < 1 or int(dia) > 31:
            return False

        return ano+'-'+str(meses[mes])+'-'+dia+hora

    r = re.findall("([0-9]{1,2})(\\/)([0-9]{1,2})(\\/)([0-9]{4})", dia_base, re.IGNORECASE | re.DOTALL)
    if r:
        dia = dia_base.split("/")
        dia.reverse()
        return r[0][4]+"-"+r[0][2]+"-"+r[0][0]+hora
        # return "-".join(dia)+hora

    r = re.findall("(\\d+)(\\s+)(de)(\\s+)([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ]+)(\\s+)(de)(\\s+)(\\d+)", dia_base, re.IGNORECASE | re.DOTALL)
    if r:
        ano = r[0][8]
        mes = r[0][4].lower()
        dia = r[0][0]

        if int(ano) < 1970 or int(ano) > 2090 or int(dia) < 1 or int(dia) > 31:
            return False

        return ano+'-'+str(meses[mes])+'-'+dia+hora

    return False

def dias_uteis(dia, dias_soma):
    um_dia = timedelta(days=(-1 if dias_soma < 0 else 1))

    d = 1
    dias_soma = dias_soma * -1 if dias_soma < 0 else dias_soma
    while d <= dias_soma:
        dia += um_dia
        if dia.weekday() in (5, 6):
            d -= 1
        d += 1

    return dia


# DETECTA E RETORNA AS INFORMAÇÕES DE AUDIENCIA CONTIDAS EM UMA STRING
def localiza_audiencia(esp, formato_data='%d/%m/%Y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)', reverse=False):
    esp = esp.upper()
    aud = {}

    r = re.search(formato_re, esp, re.IGNORECASE | re.DOTALL)
    if r is None:
        return False

    reg_data = r.group(0)
    reg_data = reg_data.upper().replace(' HORA ',' ').replace(' ÀS ',' ')
    data_tj = datetime.strptime(reg_data, formato_data)
    aud['prp_data'] = data_tj

    for status in dados_audiencia['status']:
        if esp.find('SERÁ REALIZADA') > -1 or esp.find('SERA REALIZADA') > -1 or esp.find('SER REALIZADA') > -1:
            aud['prp_status'] = 'Designada'
        if esp.find(status.upper()) > -1:
            aud['prp_status'] = status
            break

    for tipo in dados_audiencia['tipo']:
        b = esp.rfind(tipo.upper()) if reverse else esp.find(tipo.upper())
        if b > -1:
            if tipo == 'Tipo da Audiência: Una':
                tipo = 'Una'
            aud['prp_tipo'] = tipo
            if find_string(esp,('TELEPRESENCIAL','AUDIÊNCIA VIDEOCONFERÊNCIA')):
                aud['prp_tipo'] += " (Telepresencial)"
            elif find_string(esp,('MODALIDADE: SEMIPRESENCIAL',)):
                aud['prp_tipo'] += " (Semipresencial)"
            elif find_string(esp,('MODALIDADE: VIRTUAL',)):
                aud['prp_tipo'] += " (Virtual)"''
            break

    return aud

# LOCALIZA A COMARCA EM UMA STRING
def localiza_comarca(texto, uf):
    texto = texto.upper()
    if texto.upper().find('CAPITAL') > -1:
        return capitais[uf]

    if uf in cidades:
        for c in cidades[uf]:
            if texto.upper().find(c.upper()) > -1:
                return cidades[uf][c]

    # if texto.upper().find(capitais[uf].upper()) > -1:
    #     return capitais[uf]

    inicio = ['Cartas Precatórias Cíveis e Criminais de ','Comarca de', 'Cível de', 'Civel de', '- ', 'Central de', 'especiais de ', 'Especial de', 'Consumo de ', 'Criminal de ', 'Vara de', 'VARA UNICA DE', 'VARA ÚNICA DE', 'Vara Cível da Comarca', 'Criminal do', 'Cível do', 'J.E. Civel ', 'Fórum de ', 'Escrivania de','Foro de ','º jef de ','Juizado Especial Cível ','Jecc De ','ª Vara Do Trabalho De','Vara Do Trabalho De','Falências E Recuperações Judiciais De','Regional Do','Regional Da']
    fim = [' - Fórum', ' - Juizado','- Vara d','- Varas', '- Vara Cível', '- Complexo Judiciário', ' - Justiça Comum', ' - JECC', ' JECC de', ' - Juizados','(\\s+)(\\-)(\\s+)(\\d+)(º JUIZADO)','(\\s+)(\\-)(\\s+)(\\d+)(ª VARA CÍVEL)','(\\s+)(\\-)(\\s+)(\\d+)(ª VARA DA )','(\\s+)(\\-)(\\s+)(\\d+)(ª VARA DE )','(\\s+)(\\-)(\\s+)(\\d+)(º CEJUSC)',' Anexo I',' - Vara Judicial',' - Unidades dos Juizados']

    for f in fim:
        if f.find('\\') == -1:
            f = f.upper()

        r = re.search(f, texto)
        if r:
            sgn = r.group(0)
            p = texto.find(sgn)
            texto = texto[:p]
            break

        # p = texto.find(f.upper())
        # if p > -1:
        #     texto = texto[:p]
        #     break

    for i in inicio:
        p = texto.find(i.upper())
        if p > -1:
            texto = texto[p+len(i):]
            break

    texto = texto.replace('(VESP)','').replace('(MAT)', '').replace('JUIZADOS', '')
    return texto.strip().title()

# CORTA A STRING SEM TRUNCAR PALAVRA
def corta_string(texto, chars=100, sufixo='', corta_se_branco=False):
    if len(texto) <= chars:
        return texto

    chars += len(sufixo)
    result = ' '.join(texto[:chars+1].split(' ')[0:-1]) + sufixo

    if corta_se_branco and result == '':
        result = remove_acentos(texto)
        return result[:chars+1] + sufixo

    return result


# CONFERE SE EXISTE A PASTA DE DOWNLOAD. SE JÁ EXISTIR, LIMPA A PASTA
def create_folder(pasta_download, pasta_intermediaria=None, clear_if_exists=True):
    if not os.path.isdir(pasta_download):
        os.makedirs(pasta_download)
    else:
        if clear_if_exists:
            limpar_pasta(pasta_download)

    if pasta_intermediaria is not None:
        if not os.path.isdir(pasta_intermediaria):
            os.makedirs(pasta_intermediaria)
        else:
            if clear_if_exists:
                limpar_pasta(pasta_intermediaria)

# AGUARDA O TÉRMINO DO DOWNLOAD DO ARQUIVO
def aguarda_download(pasta, quantidade=1, tempo=240, latencia=0.5, tempo_nao_iniciado=30):
    inicio = time.time()
    tempo = tempo - 10
    while True:
        try:
            files = os.listdir(pasta)
            break
        except:
            tempoTotal = time.time() - inicio
            if tempoTotal >= tempo_nao_iniciado:
                print('Download nao iniciado')
                limpar_pasta(pasta)
                return False
            pass

    while len(files) == 0:
        time.sleep(latencia)
        files = os.listdir(pasta)
        tempoTotal = time.time() - inicio
        if tempoTotal >= tempo_nao_iniciado:
            print('Download nao iniciado')
            limpar_pasta(pasta)
            return False

    tmp = True
    tmp2 = False
    arq = None
    while (len(files) != quantidade and quantidade > 0) or tmp:
        time.sleep(latencia)
        files = os.listdir(pasta)
        arq = None

        if len(files) > quantidade:
            achei = False
            for nr_arq in files:
                if nr_arq.endswith('.tmp') or nr_arq.endswith('.crdownload') or nr_arq.endswith('.part'):
                    achei = True

            if not achei:
                limpar_pasta(pasta)
                raise Exception("Mais de um arquivo localizado na pasta de download")

        if len(files) > 0:
            for nr_arq in files:
                if tmp2:
                    time.sleep(0.2)
                    tmp = False

                if nr_arq.endswith('.crdownload'):
                    arq = nr_arq

                # if nr_arq == 'documentoProcessual' or nr_arq == 'ProcessoDocumentoBin':
                #     break
                if nr_arq.endswith('.tmp') or nr_arq.endswith('.crdownload') or nr_arq.endswith('.part'):
                    tmp = True
                    break
                elif not os.path.isfile(pasta+'\\'+nr_arq):
                    tmp = True
                    break

                try:
                    os.rename(pasta+'\\'+nr_arq, pasta+'\\'+nr_arq)
                except:
                    tmp = True
                    break

                time.sleep(0.2)
                tmp2 = True

        tempoTotal = time.time() - inicio
        if tempoTotal >= tempo and tmp:
            if arq is not None:
                try:
                    size1 = os.path.getsize(pasta + '\\' + arq)
                except:
                    continue
                time.sleep(5)
                try:
                    size2 = os.path.getsize(pasta + '\\' + arq)
                except:
                    continue
                if size2 - size1 > 5000:
                    inicio = time.time()
                    continue
            print('Tempo Limite de resposta atingido durante o download')
            limpar_pasta(pasta)
            return False

    files = os.listdir(pasta)
    size = os.path.getsize(pasta + '\\' + files[0])

    if size == 0:
        limpar_pasta(pasta)
        return False

    return True

# RETORNA O MES ANTERIOR AO ATUAL
def mes_anterior():
    today = datetime.today()

    if today.month == 1:
        one_month_ago = today.replace(year=today.year - 1, month=12)
    else:
        extra_days = 0
        while True:
            try:
                one_month_ago = today.replace(month=today.month - 1, day=today.day - extra_days)
                break
            except ValueError:
                extra_days += 1

    return one_month_ago

# LOCALIZA O TIPO DE ACOMPANHAMENTO DO PJE
def get_tipo_pje(texto):
    texto = texto.replace('<strike>', '')
    texto = texto.replace('</strike>', '')
    pos = texto.find(' - ')
    textoup = texto.upper()
    if pos > -1 and pos < 50:
        return texto[:pos].strip()

    if len(texto) < 30:
        return texto

    for t in tipos_pje:
        if textoup.find(t.upper()) > -1:
            return t

    return corta_string(texto, 100)


# LOCALIZA O STATUS NAS MOVIMENTAÇÕES
def get_status(movs, status_atual, considera_sentenca=True, grau=1, somente_tipo=False):
    for m in movs:
        if 'esp' in m:
            texto = m['esp']
        else:
            texto = m['acp_esp']
            if m['acp_tipo'] is not None:
                texto = m['acp_tipo'] + ' ' + m['acp_esp']

        if somente_tipo:
            texto = m['acp_tipo']

        if find_string(texto, ('DESARQUIVAMENTO', 'DESARQUIVADO', 'REATIVADO')):
            if not find_string(texto, ('SOLICITAÇÃO DE DESARQUIVAMENTO','PETIÇÃO DESARQUIVAMENTO','PETIÇÃODESARQUIVAMENTO')):
                return 'Ativo'

        if grau == 2:
            if find_string(texto, ('Arquivamento Definitivo','ARQUIVADO', 'BAIXA','Cancelamento do Processo','Remetidos os Autos para a Primeira Instância','Processo Migrado PJE')) or texto == 'Arquivamento':
                return 'Encerrado'

        if texto == 'Arquivamento':
            return 'Arquivado'

        if find_string(texto, ('DETERMINADO O ARQUIVAMENTO', 'ARQUIVADO',)):
            return 'Arquivado'

        'Arquivamento'



        if considera_sentenca and grau == 1:
            if find_string(texto, ('EXTINTO O PROCESSO', 'BAIXA DEFINITIVA',)):
                return 'Arquivado'

    return status_atual if status_atual is not None else 'Ativo'


# CRIA NOVO NOME PARA O ARQUIVO E TRANSFERE PARA A PASTA CORRETA
def trata_arquivo(nome_atual, origem, destino, ext_padrao='pdf'):
    # CAPTURA EXTENSÃO DO ARQUIVO
    print('Tratando '+nome_atual)
    # if nome_atual == 'documentoProcessual' or nome_atual == 'ProcessoDocumentoBin':
    #     ext = '.pdf'

    if nome_atual == 'pdf':
        ext = '.pdf'
    else:
        rf = nome_atual.rfind('.')
        if rf == -1 or rf < len(nome_atual) - 6:
            ext = '.'+ext_padrao
        else:
            ext = nome_atual[rf:]
            ext = ext.replace("'",'')

    # GERA UUID A PARTIR DA HORA
    uid1 = str(uuid.uuid1())
    rf = uid1.rfind('-')
    uid1 = uid1[:rf]

    # GERA UUID A PARTIR DO NOME ORIGINAL
    uid5 = str(uuid.uuid5(uuid.NAMESPACE_URL, nome_atual))
    rf = uid5.rfind('-')
    uid5 = uid5[rf:]

    # CONCATENA OS UUID E A EXTENSÃO
    arquivo = uid1+uid5+ext
    os.rename(origem + '\\' + nome_atual, origem + '\\' + arquivo)
    # print(arquivo)
    shutil.move(os.path.join(origem, arquivo), destino)
    limpar_pasta(origem)
    return arquivo

# TRANSFERE ARQUIVOS DE UMA PASTA PARA OUTRA
def move_arquivos(source_dir, target_dir):
    file_names = os.listdir(source_dir)

    for file_name in file_names:
        shutil.move(os.path.join(source_dir, file_name), target_dir)

    shutil.rmtree(source_dir)


# PROCURA UMA OU MAIS OCORRENCIA DE STRING EM OUTRA STRING
def find_string(texto, lista, upper=True, exato=False, signosUpper=False):
    if len(lista)==0:
        return False

    if upper and not signosUpper:
        texto = texto.upper()

    for t in lista:
        tt = t.upper() if upper or signosUpper else t
        if exato:
            if tt == texto:
                return tt, 0
        else:
            f = texto.find(tt)
            if f > -1:
                return tt, f

    return False

# REMOVE AS TAGS HTML DEIXANDO SOMENTE O TEXTO
def strip_html_tags(text):
    text = html.unescape(text)
    text = text.replace('\r',' ').replace('\n',' ')
    text = text.replace('  ',' ')
    text = text.replace('\t','').replace('&#x27;','').replace("'",'').replace('Ã\\x8','Á')
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    tag_re = tag_re
    # Remove well-formed tags, fixing mistakes by legitimate users
    no_tags = tag_re.sub('', text)

    # Clean up anything else by escaping
    texto = cgi.html.escape(no_tags)
    texto = texto.replace('&nbsp;',' ').replace('&gt;','>').replace('&lt;','<')
    return texto.strip()

# SALVA OCORRENCIA EM ARQUIVO DE LOG
def save_log(mensagem, estado, plataforma, prc_id, ignorar_erros_conhecidos=True):
    if ignorar_erros_conhecidos:
        if find_string(mensagem, ('tab crashed','Inspector.detached event','unable to discover open window','unable to discover open pages','Failed to create Chrome process','Connection aborted','cannot determine loading status from tab crashed','session deleted because of','SessionNotCreatedException','chrome not reachable','Can not connect to the Service chromedriver','SessionNotCreatedException','chrome.exe is no longer running','chromedriver unexpectedly exited','Unable to receive message from renderer','ConnectionResetError','Não há recursos de memória disponívei','SessionNotCreatedException','Service chromedriver unexpectedly exited','O arquivo de paginação é muito pequeno para que esta operação seja concluída','cannot activate web view','DevToolsActivePort file doesn','unable to connect to renderer','InvalidSessionIdException','ERR_CONNECTION_TIMED_OUT','ERR_CONNECTION_REFUSED','Timed out receiving message','Falha de vínculo de comunicação','Failed to establish a new connection','Foi forçado o cancelamento de uma conexão','Não foi possível abrir uma conexão','tempo limite do logon expirou','O servidor não foi encontrado ou não está acessível','ERR_INTERNET_DISCONNECTED','ERR_CONNECTION_RESET')):
            return
    hoje = datetime.now()
    dia = hoje.strftime('%d/%m/%Y %H:%M')
    with open('C:\\temp\\log_' + estado + '_' + str(plataforma) + '.csv', 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

        spamwriter.writerow([dia, prc_id, mensagem])

# APAGA TODOS OS ARQUIVOS DE UMA PASTA
def limpar_pasta(caminho):
    for filename in os.listdir(caminho):
        filepath = os.path.join(caminho, filename)
        try:
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)
        except:
            CriticalException("Erro ao apagar arquivos",'','',0,False)


# CANCELA CARREGAMENTO DA PÁGINA
def enviar_comando(process_children, tecla='VK_ESCAPE'):
    import win32gui
    import win32con
    import win32api
    import win32process

    vk_key = getattr(win32con, tecla)

    def get_hwnds_for_pid(pid):
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds


    for child in process_children:
        hwnds = get_hwnds_for_pid(child.pid)
        # print(hwnds)
        for hwnd in hwnds:
            text = win32gui.GetWindowText(hwnd)
            if text.find('Chrome') > -1:
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)


# SALVA DADOS DO PROCESSO EM PLANILHA
def salvar_planilha(processo, data_proc, responsaveis, plataforma):
    if 'prc_segredo' not in data_proc:
        data_proc['prc_segredo'] = None
    if 'prc_prioridade' not in data_proc:
        data_proc['prc_prioridade'] = None
    if 'prc_valor_causa' not in data_proc:
        data_proc['prc_valor_causa'] = None
    if 'prc_classe' not in data_proc:
        data_proc['prc_classe'] = ''
    if 'prc_assunto' not in data_proc:
        data_proc['prc_assunto'] = ''

    linha = [processo['prc_id'], processo['prc_sequencial'], data_proc['prc_numero2'], data_proc['prc_status'], data_proc['prc_serventia'], data_proc['prc_comarca2'], data_proc['prc_classe'].replace('\n', '').replace('\r', ''), data_proc['prc_assunto'].replace('\n', '').replace('\r', ''), data_proc['prc_valor_causa'], str(data_proc['prc_segredo']),
             str(data_proc['prc_prioridade']), data_proc['prc_distribuicao'],  data_proc['prc_promovente'],  data_proc['prc_cpf_cnpj'],  data_proc['prc_promovido'],  data_proc['prc_cnpj_promovido']]

    for a in responsaveis:
        linha.append(a['prr_nome'])
        linha.append(a['prr_oab'])

    with open('C:\\temp\\campos_' + str(plataforma) + '_' + processo['prc_estado'] + '.csv', 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        try:
            spamwriter.writerow(linha)
        except:
            pass

def trata_path(path, url_site=False):
    if url_site:
        path = path.replace('\\', '/')
    else:
        path = path.replace('\/', '\\')
        path = path.replace('//', '/')
        path = path.replace('/', '\\')
        path = path.replace('\\\\', '\\')

    if path.find('\\') == 0:
        path = '\\'+path

    return path

def remove_acentos(texto):
    # return unidecode('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def get_tipo_partes(tipo=None, grau=1):
    titulo_partes = {
        'ignorar': ('Beneficiário', 'Administrador', 'Síndico', 'Cônjuge', 'Alienante', 'Ass Def', 'Def. Públic','Defª. Públic', 'Defensor','Ass.M.P.', 'Depositário', 'Assistente', 'Juízo Deprecant', 'Informante', 'Complementares', 'MPAM', 'Ministério Público', 'Testemun', 'Advogad', 'Arrematante', 'Leiloeiro', 'Perito', 'Curad', 'Defensor públic', 'Def. Púb.', 'Perit', 'Herdeiro', 'Criança', 'Advogada','Procª. Justiça' ,'Proc. Justiça', 'Estagiári','Testamenteira', 'Cur. Esp.', 'Cur. Especial', 'Reconvinte', 'Reconvind','Custos legis','Adesivo','Defª. Pú.','Proc. Es.','Ajustar','coator',),
        'ativo': ('Litisconsorte Ativo', 'Impugnante', 'LitsAtiv', 'Impetran', 'Notificante', 'LitisAtiv', 'Confrontante', 'Promotor', 'Consgte', 'Ativo', 'Denunciante', 'Solicitante', 'Arrolante', 'Promovente', 'exequente', 'Exeqüente', 'requeren', 'autor', 'reclaman', 'Exeqte', 'Reqte', 'Credor', 'Reclamte', 'Interpte', 'Declarante', 'Embargan', 'Agravante', 'Vítima','Usucpte','Opoente','Excipien','Embte.'),
        'passivo': ('Litisconsorte Passivo', 'Impugnad', 'LitsPassiv','Passiv', 'Impetrad', 'Confrontado', 'Consignado', 'Passivo', 'Denunciad', 'Solicitad', 'Arrolado', 'Promovido', 'Execdo', 'Execda', 'executad', 'requerid', 'ré', 'reclamad', 'Exectd', 'Reqd', 'Proprietário', 'Devedor', 'Reclamd', 'Interpda', 'Declarado', 'Embargad', 'Agravad', 'REU','Usucapia.','Denuncia.','Reconhec.','Oposto','Excepto'),
        'terceiro': ('Aut Pl','Inventariante','Sucessor','TercNaInt', 'Intrsdo', 'Terc.Int', 'Terceiro', 'Intssado', 'Interessad', 'TerInt', 'Interesd', 'Intssada', 'Terceiro Interessado', 'Cientificado Obrigatório', 'Representante', 'Repte', 'Represte.', 'Represen', 'RepreLeg','Preposto','Interess.','Herdeira','AssLitisc')
    }

    if grau == 2:
        titulo_partes['ativo'] += ('Apte/RdoAd','Apte/Apda','Apte/Apdo','RECORRENTE', 'EMBARGANTE', 'APELANTE', 'AGRAVANTE', 'RECLAMANTE', 'REQUERENTE', 'Confrontante', 'Promotor', 'Consgte', 'Ativo', 'Denunciante', 'Solicitante', 'Arrolante', 'Promovente', 'exequente', 'Exeqüente', 'requerente', 'autor', 'reclamante', 'Exeqte', 'Reqte', 'Credor', 'Reclamte','Interpte','ApteRteAds','Suscitante','Apte/Apdo/RdoAd','Rcte/Ades')
        titulo_partes['passivo'] += ('Apdo/RteAd','Apda/RteAd','Apda/Apte','Apdo/Apte','RECORRID', 'EMBARGADO', 'APELAD', 'AGRAVAD', 'RECLAMAD', 'REQUERID', 'Confrontad', 'Consignad', 'Passiv', 'Denunciad', 'Solicitad', 'Arrolad', 'Promovid', 'executad', 'requerid', 'ré', 'reclamad', 'Exectd', 'Reqd', 'Proprietário', 'Devedor', 'Reclamd', 'Interpda','Apdo/RteAd','Suscitado','ApdoApteRt','Rcda/Ades')

    if tipo is None:
        return titulo_partes

    return titulo_partes[tipo]

def format_number_br(valor):
    valor = f'{valor:_.2f}'
    return valor.replace('.', ',').replace('_', '.')

def create_password():
    import random
    import string
    result_str = ''.join((random.choice(string.ascii_uppercase) for i in range(2)))
    result_str += ''.join((random.choice(string.ascii_lowercase) for i in range(3)))
    result_str += ''.join((random.choice(string.punctuation) for i in range(2)))
    result_str += ''.join((random.choice(string.digits) for i in range(3)))
    print(result_str)
    result_str = ''.join(random.sample(result_str, 10))
    print(result_str)
    return result_str

# TRATAR ESTADOS
def tratar_estado(estado):
    estado = remove_acentos(estado)
    estado.upper()
    estado_sigla = {
        'ACRE': 'AC', 'ALAGOAS': 'AL',
        'AMAPA': 'AP', 'AMAZONAS': 'AM',
        'BAHIA': 'BA', 'DISTRITO FEDERAL': 'DF',
        'CEARA': 'CE', 'ESPIRITO SANTO': 'ES',
        'GOIAS': 'GO', 'MARANHAO': 'MA',
        'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS',
        'MINAS GERAIS': 'MG', 'PARAIBA': 'PB',
        'PARANA': 'PR', 'PARA': 'PA',
        'PERNAMBUCO': 'PE', 'PIAUI': 'PI',
        'RIO DE JANEIRO': 'RJ', 'RIO GRANDE DO NORTE': 'RN',
        'RIO GRANDE DO SUL': 'RS', 'RONDONIA': 'RO',
        'RORAIMA': 'RR', 'SANTA CATARINA': 'SC',
        'SAO PAULO': 'SP', 'SERGIPE': 'SE', 'TOCANTINS': 'TO', 'BRASILIA': 'DF'
    }

    return estado_sigla[estado]

# CONVERTE STRING DE VALOR PT-BR PARA FLOAT
def valor_br(valor):
    valor = re.sub("[^0-9.,]", "", valor)
    if re.search('(\d+)(,)([0-9]{3})(.)', valor):
        valor = valor.replace(',', '')
    else:
        try:
            return float(valor)
        except:
            pass
        valor = valor.replace('.', '')
        valor = valor.replace(',', '.')

    return float(valor)

# CONVERTE HTML PARA PDF
def html_to_pdf(conteudo, output):
    """
    Generate a pdf using a string content

    Parameters
    ----------
    content : str
        content to write in the pdf file
    output  : str
        name of the file to create
    """
    # Open file to write
    result_file = open(output, "w+b") # w+b to write in binary mode.

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
            conteudo,                   # the HTML to convert
            dest=result_file           # file handle to recieve result
    )

    # close output file
    result_file.close()

    result = pisa_status.err

    if not result:
        print("PDF Criado com sucesso")
    else:
        print("Erro ao criar arquivo PDF")

    # return False on success and True on errors
    return result

# CONVERTE HTML PARA PDF
def pdf_to_img(input, output_url):
    import fitz
    pdffile = input
    doc = fitz.open(pdffile)
    out = fitz.open()
    for page_index in range(doc.pageCount):
        page = doc.load_page(page_index)  # number of page
        pix = page.get_pixmap()
        output = output_url+"\\outfile"+str(page_index)+".png"
        pix.save(output)
        imgdoc = fitz.open(output_url+"\\outfile"+str(page_index)+".png")
        pdfbytes = imgdoc.convert_to_pdf()
        imgpdf = fitz.open("pdf", pdfbytes)
        out.insert_pdf(imgpdf)

    doc.close()
    out.save(input)
    out.close()

def cria_html_diario(drp):
    drp_conteudo = drp['drp_conteudo'].replace('htm','')
    html = """<html>
    <head>
        <meta charset="utf-8">
        <title>"""+drp['drp_processo']+"""</title>
    </head>
    <body>
        <h1 style="color:#3b3b3b;font-size:24px;text-align:center;">"""+drp['drp_titulo']+"""</h1>
        <h2 style="color:#595959;">"""+drp['drp_subtitulo']+"""</h1>
        <h3 style="color:#737373;">"""+drp['drp_enunciado']+"""</h1>
        <h1 style="color:#566a87;font-size:20px;">"""+drp['drp_processo']+"""</h2>
        <p>"""+drp_conteudo+"""</p>
    </body>
    </html>"""

    return html
