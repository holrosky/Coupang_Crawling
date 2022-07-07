import base64
import hashlib
import json
import time

import requests as requests
from selenium import webdriver

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import hmac

def send_key(xpath, keys):
    driver.find_element(By.XPATH, xpath).send_keys(keys)

def click(xpath):
    driver.find_element(By.XPATH, xpath).click()

def wait_until_clickable(time, xpath):
    WebDriverWait(driver, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))

def is_logged_out():
    driver.refresh()

    while True:
        try:
            wait_until_clickable(1, "//input[@id='username']")
            return True
        except:
            pass

        try:
            wait_until_clickable(1, "//span[@id='js-voucher-before-used-count']")
            return False
        except:
            pass

def is_there_order():
    wait_until_clickable(20, "//button[@class='btn btn-st05 js-search-button']")

    num_of_order = int(driver.find_element(By.XPATH, "//span[@id='js-voucher-before-used-count']").text)

    if num_of_order == 0:
        return False

    return True

def parse_order_data():
    while len(driver.window_handles) < 2:
        time.sleep(0.5)

    result = []

    driver.switch_to.window(driver.window_handles[-1])

    try:
        wait_until_clickable(2, "//button[@class='btn-s-ty02 js-use-ticket']")
    except Exception as e:
        return result

    cnt = len(driver.find_elements(By.XPATH, "//table[@class='cancle-table sub-table']"))

    for i in range(cnt):
        temp_dict = dict()
        pcode_text = driver.find_elements(By.CLASS_NAME, 'cancle-table')[-1].text.split(': ')
        temp_dict['pcode'] = pcode_text[-1]
        temp_dict['pname'] = driver.find_elements(By.XPATH, "//span[@class='tit-detail']")[0].text
        temp_dict['ordernum'] = driver.find_elements(By.XPATH, "//td[@class='tit-sub']")[5].text
        temp_dict['orderdate'] = ''
        temp_dict['ordername'] = driver.find_elements(By.XPATH, "//td[@class='tit-sub']")[0].text
        temp_dict['orderhtel'] = driver.find_elements(By.XPATH, "//td[@class='tit-sub']")[2].text
        temp_dict['orderemail'] = driver.find_elements(By.XPATH, "//td[@class='tit-sub']")[3].text
        temp_dict['ticketnum'] = driver.find_elements(By.CLASS_NAME, 'sub-table')[i].find_element(By.CLASS_NAME, 'ticket-title').find_element(By.CLASS_NAME, 'padding-42').text
        temp_dict['optionname'] = driver.find_elements(By.XPATH, "//td[@class='subtitle']")[1].text
        start_date, end_date = driver.find_elements(By.XPATH, "//table[@class='cancle-table']")[1].find_elements(By.CLASS_NAME, 'tit-sub')[5].text.split('~')
        temp_dict['use_sdate'] = start_date.strip(' ')
        temp_dict['use_edate'] = end_date.strip(' ')
        temp_dict['price_sale'] = int(driver.find_elements(By.XPATH, "//table[@class='cancle-table sub-table']")[i].find_elements(By.CLASS_NAME, 'ticket-sub-tr')[1].find_element(By.CLASS_NAME, 'padding-42').text[:-1].replace(',', ''))
        temp_dict['price_input'] = int(driver.find_elements(By.XPATH, "//table[@class='cancle-table sub-table']")[i].find_elements(By.CLASS_NAME, 'ticket-sub-tr')[1].find_elements(By.CLASS_NAME, 'tit-sub')[1].text[:-1].replace(',', ''))

        result.append(temp_dict)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    for each in result:
        each['orderdate'] = driver.find_elements(By.CLASS_NAME, 'reservation-bold-font')[10].text

    print(result)
    return result

def log_in():
    print('Logging in...')

    wait_until_clickable(20, "//input[@id='username']")
    time.sleep(1)

    with open("config.json", "r", encoding='utf-8') as st_json:
        json_data = json.load(st_json)

    coupang_id = json_data['coupang_id']
    coupang_pwd = json_data['coupang_pwd']
    sms_api_url = json_data['sms_api_url']
    sms_api_key = json_data['sms_api_key']

    send_key("//input[@id='username']", coupang_id)
    send_key("//input[@id='password']", coupang_pwd + Keys.ENTER)

    wait_until_clickable(20, "//input[@id='btnSms']")

    click("//input[@id='btnSms']")

    wait_until_clickable(20, "//input[@id='auth-mfa-code']")

    while True:
        try:
            time.sleep(7)

            response = requests.get(url=sms_api_url, params={'key': sms_api_key})

            auth_code = response.json()
            print('Auth code : ' + str(auth_code['auth']))

            send_key("//input[@id='auth-mfa-code']", auth_code['auth'] + Keys.ENTER)

            wait_until_clickable(20, "//img[@alt='쿠팡로고']")

            break
        except Exception as e:
            print(e)
            try:
                wait_until_clickable(20, "//input[@id='auth-mfa-code']")
            except Exception as e:
                driver.get(url=URL)
                log_in()
                return

    driver.get(url=URL)

    wait_until_clickable(20, "//span[@id='js-voucher-before-used-count']")

    print('Logging in done!')

if __name__ == "__main__":
    with open("config.json", "r", encoding='utf-8') as st_json:
        json_data = json.load(st_json)

    URL = 'https://with.coupang.com/reservations/by-inventory-type?productType=TICKET&inventoryType=PERIOD&dateType=month&orderStatus=CONFIRM_PENDING,CONFIRMED'

    post_api_url = json_data['post_api_url']
    secrete_key = json_data['secrete_key']
    auth_key = json_data['auth_key']
    encrypt_key = json_data['encrypt_key']

    driver = webdriver.Chrome(executable_path='chromedriver')
    driver.get(url=URL)

    while True:
        if is_logged_out():
            log_in()

        if is_there_order():
            click("//button[@class='btn-s-ty02 display-b m0-auto js-detail']")

            parse_data = {'secretkey': secrete_key, 'item': list()}

            for each in parse_order_data():
                parse_data['item'].append(each)

            if len(parse_data['item']) != 0:
                driver.find_elements(By.NAME, 'selectVoucherOrder')[1].click()
                click("//button[@class='btn btn-st01  green js-use-ticket-list']")
                wait_until_clickable(20, "//button[@class='btn btn btn-st01 green']")
                click("//button[@class='btn btn btn-st01 green']")

                digest = hmac.new(encrypt_key.encode('utf-8'), str(parse_data).encode('utf-8'), hashlib.sha256).digest()
                digest_b64 = base64.b64encode(digest)  # bytes again
                Hmac = auth_key + ':' + digest_b64.decode('utf-8')

                header = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': auth_key,
                    'Hmac': Hmac
                }

                post_result = requests.post(url=post_api_url, headers=header, data=json.dumps(parse_data))

                print(Hmac)
                print(post_result.json())

            else:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        else:
            time.sleep(1)

