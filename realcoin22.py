import time
import pyupbit
import datetime
import schedule
import requests
from fbprophet import Prophet


#사용자의 Access key
access = "your-access"
#사용자의 Secret key
secret = "your-secret"

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
 
myToken = "Your-Token"
def dbgout(message):
    
    """Send it to the slack at the same time."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    post_message(myToken,"#coin", strbuf)




def get_start_time(ticker):
    #시작 시간
    """Check the start time."""
    X = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = X.index[0]
    return start_time

def get_balance(ticker):
    #잔고 조회
    """Check your balance."""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_target_price(ticker, k):
    #변동성 돌파 전략 이용. 변동성 K값 구하기.
    """The purchase target is inquiry."""
    X = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = X.iloc[0]['close'] + (X.iloc[0]['high'] - X.iloc[0]['low']) * k
    return target_price

def get_current_price(ticker):
    #현재가격
    """Current price inquiry."""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    #Prohbet으로 종가 예측
    """The predicted closing price."""
    global predicted_close_price
    X = pyupbit.get_ohlcv(ticker, interval="minute60")
    X = X.reset_index()
    X['ds'] = X['index']
    X['y'] = X['close']
    data = X[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price("KRW-ETH")
schedule.every().hour.do(lambda: predict_price("KRW-ETH"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Auto trade start!")

#시작시 slack으로 알림
post_message(myToken,"#coin", "Auto trade start!")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-ETH")
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-ETH", 0.5) #변동성 K값
            current_price = get_current_price("KRW-ETH")
            if target_price < current_price and current_price < predicted_close_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-ETH", krw*0.9995)
                    buy = upbit.buy_market_order("KRW-ETH", krw*0.9995)
                    post_message(myToken,"#coin", "buy : " +str(buy))
        else:
            eth = get_balance("ETH")
            if eth > 0.00008:
                upbit.sell_market_order("KRW-ETH", eth*0.9995)
                sell = upbit.sell_market_order("KRW-ETH", eth*0.9995)
                post_message(myToken,"#coin", "sell : " +str(sell))
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)