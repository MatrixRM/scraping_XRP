import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from twilio.rest import Client  # Biblioteca para envio de SMS pelo Twilio
from dotenv import load_dotenv  # Biblioteca para carregar variáveis de ambiente de um arquivo .env
import atexit

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do WebDriver para o navegador Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Executa sem interface gráfica
options.add_argument("--disable-gpu")  # Evita problemas em sistemas sem GPU
options.add_argument("--no-sandbox")  # Necessário para execução em ambientes limitados
options.add_argument("--disable-dev-shm-usage")  # Melhora desempenho em contêineres
options.add_argument('--ignore-certificate-errors')  # Ignora erros de SSL
options.add_argument('--ignore-ssl-errors')  # Ignora erros de SSL adicionais
options.add_argument('--disable-web-security')  # Desabilita a segurança da Web (não recomendado em produção)

# Inicializa o WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Garante que o WebDriver seja fechado quando o script terminar
atexit.register(driver.quit)

# Carrega as configurações do Twilio a partir do arquivo .env
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')  # Número adquirido no Twilio
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')  # Número que receberá o SMS

# Verifica se todas as variáveis de ambiente foram carregadas corretamente
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, YOUR_PHONE_NUMBER]):
    raise EnvironmentError("Verifique se todas as variáveis do .env estão configuradas corretamente.")

# Inicializa o cliente Twilio
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# URL do site que será acessado para capturar os preços
url = "https://www.coingecko.com/pt"

# Função para capturar os preços de BTC e XRP
def fetch_prices():
    try:
        # Abre a URL no navegador
        driver.get(url)

        # Localiza e extrai o preço do BTC
        btc_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/main/div/div[5]/table/tbody/tr[1]/td[5]/span')
            )
        )
        btc_price = float(btc_element.text.replace('US$', '').replace(',', '').strip())

        # Localiza e extrai o preço do XRP
        xrp_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/main/div/div[5]/table/tbody/tr[5]/td[5]/span')
            )
        )
        xrp_price = float(xrp_element.text.replace('US$', '').replace(',', '').strip())

        return btc_price, xrp_price

    except Exception as e:
        print(f"Erro ao capturar os preços: {e}")
        return None, None

# Função para enviar um SMS com os preços atualizados
def send_sms(message):
    try:
        print(f"Enviando SMS de {TWILIO_PHONE_NUMBER} para {YOUR_PHONE_NUMBER}...")
        response = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_PHONE_NUMBER
        )
        print(f"SMS enviado com sucesso. SID: {response.sid}")
    except Exception as e:
        print(f"Erro ao enviar SMS: {e}")

# Função principal que monitora os preços e envia alertas
def monitor_prices(interval=300):
    prev_btc_price = None  # Preço anterior do BTC
    prev_xrp_price = None  # Preço anterior do XRP

    try:
        while True:
            # Obtém os preços atuais
            btc_price, xrp_price = fetch_prices()

            if btc_price is not None and xrp_price is not None:
                # Formata o timestamp atual
                timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

                # Determina a tendência de preços do BTC
                btc_trend = (
                    "alta" if prev_btc_price and btc_price > prev_btc_price
                    else "baixa" if prev_btc_price and btc_price < prev_btc_price
                    else "estavel"
                )

                # Determina a tendência de preços do XRP
                xrp_trend = (
                    "alta" if prev_xrp_price and xrp_price > prev_xrp_price
                    else "baixa" if prev_xrp_price and xrp_price < prev_xrp_price
                    else "estavel"
                )

                # Salva os preços e tendências em um arquivo de log
                with open("precos_relatorio.txt", "a") as f:
                    f.write(f"Hoje dia {timestamp} BTC esta velendo : {btc_price} ({btc_trend})\n")
                    f.write(f"Hoje dia {timestamp} XRP esta valendo: {xrp_price} ({xrp_trend})\n")

                # Cria a mensagem para enviar por SMS
                message = (
                    f"[{timestamp}] Preços atualizados:\n"
                    f"BTC: {btc_price} ({btc_trend})\n"
                    f"XRP: {xrp_price} ({xrp_trend})"
                )

                # Envia a mensagem por SMS
                send_sms(message)

                # Atualiza os preços anteriores
                prev_btc_price = btc_price
                prev_xrp_price = xrp_price

            else:
                print("Erro ao capturar preços. Tentando novamente em 5 minutos.")

            # Aguarda o intervalo especificado antes de capturar os preços novamente
            time.sleep(interval)

    finally:
        # Garante que o WebDriver seja fechado no final
        driver.quit()

# Ponto de entrada do script
if __name__ == "__main__":
    monitor_prices()
