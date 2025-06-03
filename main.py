from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

app = Flask(__name__)

def get_exchange_rate():
    url = 'https://finance.naver.com/marketindex/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    iframe = soup.find('iframe', id='frame_ex1')
    if not iframe:
        raise Exception("환율 정보 iframe을 찾을 수 없습니다.")
    iframe_url = 'https://finance.naver.com' + iframe['src']

    iframe_response = requests.get(iframe_url)
    iframe_soup = BeautifulSoup(iframe_response.text, 'html.parser')

    items = iframe_soup.select('body > div > table > tbody > tr')
    rateDict = {}
    for item in items:
        currency_title = item.select_one('td.tit').text.strip()
        rate = item.select_one('td.sale').text.strip()
        m = re.search(r'([A-Z]{3})', currency_title)
        if m:
            code = m.group(1).lower()
            if 'jpy' in currency_title.lower():
                code = 'jpy'
                rateDict[code] = float(rate.replace(",", "")) / 10
            else:
                rateDict[code] = float(rate.replace(",", "")) * 10
    return rateDict

def get_bank_info():
    csv_path = os.path.join(os.path.dirname(__file__), '은행별 환전.csv')
    df = pd.read_csv(csv_path)
    bank_list = [str(bank).strip().lower() for bank in df['은행'].tolist()]
    interestDict = {str(bank).strip().lower(): float(str(interest).replace("%", "")) for bank, interest in zip(df['은행'], df['환전 수수료'])}
    preferential_rateDict = {str(bank).strip().lower(): float(str(pref).replace("%", "")) for bank, pref in zip(df['은행'], df['최대 우대율'])}
    return bank_list, interestDict, preferential_rateDict

def calculate_to_krw(money, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict):
    rate = rateDict.get(exchangecurrency)
    if rate is None or rate == 0:
        return None
    interest = interestDict[bank]
    preferential_rate = preferential_rateDict[bank]
    aftercal = money * rate * (1 - interest / 100) * (1 - preferential_rate / 100)
    formatted = "{:,}".format(round(aftercal, 2))
    korean = number_to_korean(aftercal)
    return formatted, korean

def calculate_from_krw(money, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict):
    rate = rateDict.get(exchangecurrency)
    if rate is None or rate == 0:
        return None
    interest = interestDict[bank]
    preferential_rate = preferential_rateDict[bank]
    aftercal = money / (rate * (1 - interest / 100) * (1 - preferential_rate / 100))
    formatted = "{:,}".format(round(aftercal, 2))
    korean = number_to_korean(aftercal)
    return korean, formatted

def number_to_korean(num):
    units = ["", "만", "억", "조", "경"]
    nums = ["", "십", "백", "천"]
    result = []
    num_str = str(int(num))
    length = len(num_str)
    for i in range(0, length, 4):
        part = num_str[max(0, length - i - 4):length - i]
        if int(part) == 0:
            continue
        part_result = ""
        for j, n in enumerate(part.zfill(4)):
            if n != '0':
                part_result += ("" if n == '1' and j != 3 else n) + nums[3 - j]
        if part_result:
            result.insert(0, part_result + units[i // 4])
    return ' '.join(result) if result else '0'

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    result = None
    korean = ""  # 또는 None 등으로 초기화
    try:
        rateDict = get_exchange_rate()
    except Exception as e:
        rateDict = {}
        error = f"환율 정보를 불러올 수 없습니다: {e}"
    try:
        bank_list, interestDict, preferential_rateDict = get_bank_info()
    except Exception as e:
        bank_list, interestDict, preferential_rateDict = [], {}, {}
        error = f"은행 정보를 불러올 수 없습니다: {e}"

    if request.method == 'POST':
        try:
            money = float(request.form['money'])
            currency = request.form['currency']
            bank = request.form['bank']
            if money < 0:
                raise ValueError
            result_value, korean = calculate_to_krw(money, currency, bank, rateDict, interestDict, preferential_rateDict)
            if result_value is not None:
                result = "{:,}".format(int(money))+" "+ f"{currency.upper()} → {result_value} 원"
            else:
                error = "환율 정보를 찾을 수 없습니다."
        except Exception:
            error = "입력값을 다시 확인해주세요."

    return render_template('home.html',
                           rates=rateDict,
                           bank_list=bank_list,
                           result=result,
                           result_korean=f"한화 {korean} 원" if korean else "",
                           error=error)

@app.route('/from-krw', methods=['GET', 'POST'])
def from_krw():
    error = None
    result = None
    korean = ""
    currency = ""  # 또는 None 등으로 초기화
    try:
        rateDict = get_exchange_rate()
        bank_list, interestDict, preferential_rateDict = get_bank_info()
    except Exception as e:
        rateDict, bank_list, interestDict, preferential_rateDict = {}, [], {}, {}
        error = f"정보를 불러올 수 없습니다: {e}"

    if request.method == 'POST':
        try:
            money = float(request.form['money'])
            currency = request.form['currency']
            bank = request.form['bank']
            if money < 0:
                raise ValueError
            korean, result_value = calculate_from_krw(money, currency, bank, rateDict, interestDict, preferential_rateDict)
            if result_value is not None:
                result = "{:,}".format(int(money))+" 원 → "+ f"{result_value} {currency.upper()}"
            else:
                error = "환율 정보를 찾을 수 없습니다."
        except Exception:
            error = "입력값을 다시 확인해주세요."

    return render_template('from_krw.html',
                           rates=rateDict,
                           bank_list=bank_list,
                           input_korean=korean,
                           result=result,
                           currency=currency,
                           error=error)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=8945)


