import requests
from bs4 import BeautifulSoup
import pandas as pd

# 메시지 정의
msg = "1.해외통화->원 2.원->해외통화 3.통화단위 조회 4.은행별 환전수수료 조회 (나가기: 아무키)"
errMsg1 = "숫자 1,2,3,4만 입력"
errMsg2 = "금액수 잘못기입"
endMsg = "사용 종료"

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
currency_title = item.select_one('td.tit').text.strip() # 예: '미국 USD'
rate = item.select_one('td.sale').text.strip()
# 통화 코드 추출 (예: USD, JPY(100엔) 등)
import re
m = re.search(r'([A-Z]{3})', currency_title)
if m:
code = m.group(1).lower()
# JPY(100엔)은 별도 처리
if 'jpy' in currency_title.lower():
code = 'jpy'
rateDict[code] = float(rate.replace(",", "")) / 100
else:
rateDict[code] = float(rate.replace(",", ""))
return rateDict

def get_valid_input(prompt, valid_options):
while True:
user_input = input(prompt).strip().lower()
# 완전일치 우선
if user_input in valid_options:
return user_input
# 부분일치
matching = [opt for opt in valid_options if user_input in opt]
if len(matching) == 1:
return matching[0]
elif len(matching) > 1:
print(f"여러 항목이 일치합니다: {', '.join(matching)}")
print("더 구체적으로 입력해주세요.")
else:
print(f"일치하는 항목이 없습니다. 다음 중에서 선택해주세요: {', '.join(valid_options)}")

def calculate_exchange1(money, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict):
rate = rateDict.get(exchangecurrency)
if rate is None:
return None
interest = interestDict[bank]
preferential_rate = preferential_rateDict[bank]
aftercal = money * rate * (1 - interest / 100) * (1 - preferential_rate / 100)
return round(aftercal, 2)

def calculate_exchange2(money, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict):
rate = rateDict.get(exchangecurrency)
if rate is None:
return None
interest = interestDict[bank]
preferential_rate = preferential_rateDict[bank]
aftercal = money * (1 - interest / 100) * (1 - preferential_rate / 100) / rate
return round(aftercal, 2)

def main():
# 환율 정보 불러오기
try:
rateDict = get_exchange_rate()
except Exception as e:
print(f"환율 정보를 불러올 수 없습니다: {e}")
return

# 은행 환전 수수료 및 우대율 정보 불러오기
csv_path = r'C:\Users\Lushimiru\Desktop\currency_exchange\은행별 환전.csv'
try:
df = pd.read_csv(csv_path)
except Exception as e:
print(f"CSV 파일을 불러올 수 없습니다: {e}")
return

bank_list = [str(bank).strip().lower() for bank in df['은행'].tolist()]
interestDict = {str(bank).strip().lower(): float(str(interest).replace("%", "")) for bank, interest in zip(df['은행'], df['환전 수수료'])}
preferential_rateDict = {str(bank).strip().lower(): float(str(pref).replace("%", "")) for bank, pref in zip(df['은행'], df['최대 우대율'])}

while True:
try:
choose = int(input(msg + "\n입력: "))
except ValueError:
print(endMsg)
break
if choose == 1:
while True:
money = input("금액수 입력: ex) 1000 (나가기: q): ")
if money.lower() == 'q':
break
try:
money = float(money)
if money < 0:
raise ValueError
except ValueError:
print(errMsg2)
continue
exchangecurrency = get_valid_input("통화 종류 (ex: usd, jpy, cny, eur, ...): ", list(rateDict.keys()))
bank = get_valid_input("이용할 은행 (ex: 국민, 농협, 하나, ...): ", bank_list)
result = calculate_exchange1(money, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict)
if result is not None:
print(f"{money} {exchangecurrency.upper()} -> {result} 원")
else:
print("환율 정보를 찾을 수 없습니다.")
elif choose == 2:
while True:
moneyKor = input("금액수 입력: ex) 1000 (나가기: q): ")
if moneyKor.lower() == 'q':
break
try:
moneyKor = float(moneyKor)
if moneyKor < 0:
raise ValueError
except ValueError:
print(errMsg2)
continue
exchangecurrency = get_valid_input("통화 종류 (ex: usd, jpy, cny, eur, ...): ", list(rateDict.keys()))
bank = get_valid_input("이용할 은행 (ex: 국민, 농협, 하나, ...): ", bank_list)
result = calculate_exchange2(moneyKor, exchangecurrency, bank, rateDict, interestDict, preferential_rateDict)
if result is not None:
print(f"{moneyKor} 원 -> {result} {exchangecurrency.upper()}")
else:
print("환율 정보를 찾을 수 없습니다.")
elif choose == 3:
print('-----------------------------------------')
for code, rate in rateDict.items():
print(f"{code.upper()}: {rate}")
print('-----------------------------------------')
elif choose == 4:
print('-----------------------------------------')
for bank in bank_list:
print(f"{bank}: 수수료 {interestDict[bank]}%, 최대 우대율 {preferential_rateDict[bank]}%")
print('-----------------------------------------')
else:
print(endMsg)
break

if __name__ == "__main__":
main()