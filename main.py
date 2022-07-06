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
    driver.find_element_by_xpath(xpath).click()

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

    num_of_order = int(driver.find_element_by_xpath("//span[@id='js-voucher-before-used-count']").text)
    print(num_of_order)

    if num_of_order == 0:
        return False

    return True

def get_pcode(item_name):
    driver.refresh()
    wait_until_clickable(20, "//div[@class='all-product-modal-btn-wrapper js-view-product-list-btn']")
    click("//div[@class='all-product-modal-btn-wrapper js-view-product-list-btn']")
    wait_until_clickable(20, "//a[@id='product-list-modal-reset-button']")
    click("//a[@id='product-list-modal-reset-button']")
    wait_until_clickable(20, "//a[@id='product-list-modal-reset-button']")
    send_key("//input[@id='product-list-modal-travel-name']", item_name + Keys.ENTER)
    wait_until_clickable(20, "//button[@class='btn-s-ty03 product-list-modal-select-button']")
    click("//button[@class='btn-s-ty03 product-list-modal-select-button']")
    wait_until_clickable(20, "//button[@class='btn btn-st05 js-search-button']")

    print(driver.find_element_by_xpath("//div[@class='product-id-wrapper']").text)
    return ''


def parse_order_data():
    while len(driver.window_handles) < 2:
        time.sleep(0.5)

    result = []

    driver.switch_to.window(driver.window_handles[-1])

    # try:
    #     wait_until_clickable(2, "//button[@class='btn-s-ty02 js-use-ticket']")
    # except Exception as e:
    #     return result

    cnt = len(driver.find_elements_by_xpath("//table[@class='cancle-table sub-table']"))
    print(cnt)

    for i in range(cnt):
        temp_dict = dict()

        temp_dict['pname'] = driver.find_elements_by_xpath("//span[@class='tit-detail']")[0].text
        temp_dict['ordernum'] = driver.find_elements_by_xpath("//td[@class='tit-sub']")[5].text
        temp_dict['orderdate'] = ''
        temp_dict['ordername'] = driver.find_elements_by_xpath("//td[@class='tit-sub']")[0].text
        temp_dict['orderhtel'] = driver.find_elements_by_xpath("//td[@class='tit-sub']")[2].text
        temp_dict['orderemail'] = driver.find_elements_by_xpath("//td[@class='tit-sub']")[3].text
        temp_dict['ticketnum'] = driver.find_elements_by_class_name('sub-table')[i].find_element_by_class_name('ticket-title').find_element_by_class_name('padding-42').text
        temp_dict['optionname'] = driver.find_elements_by_xpath("//td[@class='subtitle']")[1].text
        start_date, end_date = driver.find_elements_by_xpath("//table[@class='cancle-table']")[1].find_elements_by_class_name('tit-sub')[5].text.split('~')
        temp_dict['use_sdate'] = start_date.strip(' ')
        temp_dict['use_edate'] = end_date.strip(' ')
        temp_dict['price_sale'] = int(driver.find_elements_by_xpath("//table[@class='cancle-table sub-table']")[i].find_elements_by_class_name('ticket-sub-tr')[1].find_element_by_class_name('padding-42').text[:-1].replace(',', ''))
        temp_dict['price_input'] = int(driver.find_elements_by_xpath("//table[@class='cancle-table sub-table']")[i].find_elements_by_class_name('ticket-sub-tr')[1].find_elements_by_class_name('tit-sub')[1].text[:-1].replace(',', ''))

        result.append(temp_dict)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    #pcode = get_pcode(temp_dict['item_name'])

    for each in result:
        each['orderdate'] = driver.find_elements_by_class_name('reservation-bold-font')[10].text

    print(result)
    return result

def log_in():
    print('Logging in...')

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

            wait_until_clickable(5, "//img[@alt='쿠팡로고']")

            break
        except Exception as e:
            print(e)
            try:
                wait_until_clickable(5, "//input[@id='auth-mfa-code']")
            except Exception as e:
                driver.get(url=URL)
                log_in()
                break

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

    wait_until_clickable(20, "//input[@id='username']")
    time.sleep(1)


    if is_logged_out():
        log_in()

    time.sleep(5)
    click("//button[@class='btn-s-ty02 display-b m0-auto js-detail']")

    parse_data = {'secretkey': secrete_key, 'item': list()}

    for each in parse_order_data():
        parse_data['item'].append(each)

    print(parse_data)

    with open('result.json', 'w', encoding="UTF8") as f:
        json.dump(parse_data, f, ensure_ascii=False, indent=4)

    digest = hmac.new(encrypt_key.encode('utf-8'), str(parse_data).encode('utf-8'), hashlib.sha256).digest()
    digest_b64 = base64.b64encode(digest)  # bytes again
    Hmac = auth_key + ':' + digest_b64.decode('utf-8')

    header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': auth_key,
        'Hmac': Hmac
    }

    post_result = requests.post(url=post_api_url, headers=header)

    print(Hmac)
    print(post_result)

    # while True:
    #     if is_logged_out():
    #         log_in()
    #
    #     if is_there_order():
    #         click("//button[@class='btn-s-ty02 display-b m0-auto js-detail']")
    #
    #         parse_data = {'item': list()}
    #
    #         for each in parse_order_data():
    #             parse_data['item'].append(each)
    #
    #         if len(parse_data['item']) != 0:
    #             driver.find_elements_by_name('selectVoucherOrder')[1].click()
    #             click("//button[@class='btn btn-st01  green js-use-ticket-list']")
    #             wait_until_clickable(20, "//button[@class='btn btn btn-st01 green']")
    #             click("//button[@class='btn btn btn-st01 green']")
    #
    #             # send post request here...
    #
    #             digest = hmac.new(encrypt_key.encode('utf-8'), str(parse_data).encode('utf-8'), hashlib.sha256).digest()
    #             digest_b64 = base64.b64encode(digest)  # bytes again
    #             Hmac = auth_key + ':' + digest_b64.decode('utf-8')
    #
    #             header = {
    #                 'Accept': 'application/json',
    #                 'Content-Type': 'application/json',
    #                 'Authorization': auth_key,
    #                 'Hmac': Hmac
    #             }
    #
    #             post_result = requests.post(url=post_api_url, headers=header)
    #
    #             print(Hmac)
    #             print(post_result)
    #
    #         else:
    #             driver.close()
    #             driver.switch_to.window(driver.window_handles[0])
    #
    #     else:
    #         time.sleep(5)
