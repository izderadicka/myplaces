# encoding=utf-8
'''
Created on Nov 9, 2013

@author: ivan
'''


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException,\
    NoAlertPresentException
import unittest, time, re
import os
import subprocess
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import sys
import remote
import zmq
from socket import gethostname
import signal



class TestCaseSelenium(unittest.TestCase):
    def setUp(self):
        if START_SERVERS:
            manage=os.path.join(os.path.split(__file__)[0], '../../../manage.py')
            self.web_server=subprocess.Popen(['python', manage,  'runserver_socketio', 'localhost:8001'], shell=False)
            self.process_server=subprocess.Popen(['python', manage,  'process_server'], shell=False)
        if DRIVER=='firefox':
            self.driver = webdriver.Firefox()
        elif DRIVER=="chrome":
            self.driver=webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.base_url = BASE_URL
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_interaction(self):
        cases=self._get_cases()
        self.login('admin', 'admin')
        for i in range(CYCLES):
            case=random.choice(cases)
            start=time.time()
            case()
            dur=time.time()-start
            case_name=case.__name__
            report_result(i, case_name, dur)
            print '%d - case: %s- %f' %(i, case.__name__, dur)
        
        self.logout()
    CASE_RE=re.compile(r'^case(\w+)$') 
    def _get_cases(self):
        all= CASES == "all"
        if not all:
            case_ids= map(lambda s: s.strip(), CASES.split(','))
        cases=[]    
        for name in dir(self):
            m=self.CASE_RE.match(name)
            if m and (all or m.group(1) in case_ids):
                cases.append(getattr(self, name))
        return cases
        
    def case1(self):
        driver=self.driver
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//ul[@id='groups_list']/li[2]/span" )))
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[2]/span").click()
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[2]/div[3]/div/div/div[2]").click()
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[7]/div").click()
       
        driver.find_element_by_link_text(u"×").click()

        driver.find_element_by_xpath(u"//img[@title='Bobrovská Martina,  Centrum léčebné rehabilitace']").click()
        driver.find_element_by_link_text(u"×").click()
        driver.find_element_by_xpath("//div[@id='map']/div[2]/div[2]/div").click()
        
        WebDriverWait(driver,10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#right_panel #place_search_3')))
        search=driver.find_element_by_css_selector('#right_panel #place_search_3')
        search.clear()
        search.send_keys("chrb")
        driver.find_element_by_css_selector("#places_list_wrapper > #groups_list > li > div.edit_btn.small_btn").click()
        driver.find_element_by_css_selector("input.cancel_btn").click()
        driver.find_element_by_id("logo").click()
        
    def case2(self):
        driver=self.driver
        #driver.get(self.base_url + "/mp/")
        driver.find_element_by_css_selector("div.map_btn.small_btn").click()
        actions=ActionChains(driver).move_to_element(driver.find_element_by_css_selector('div.leaflet-control-layers')).perform()
        driver.find_element_by_css_selector("div.leaflet-control-layers-overlays > label > input.leaflet-control-layers-selector").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'svg.leaflet-zoom-animated')))
        driver.find_element_by_css_selector("div.button-control.close").click()
        
    def case3(self):
        driver=self.driver
        driver.find_element_by_css_selector("#left_panel span.title").click()
        driver.find_element_by_css_selector("div.label-small").click()
        driver.find_element_by_id("place_search_1").clear()
        driver.find_element_by_id("place_search_1").send_keys("uneti\n")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[data-pk="173"]')))
        driver.find_element_by_css_selector("#right_panel span.title").click()
        driver.find_element_by_css_selector("#places_list_wrapper > #groups_list > li > div.map_btn.small_btn").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.leaflet-popup')))
        driver.find_element_by_xpath("//div[@id='map']/div[2]/div[2]/div").click()
        
        driver.find_element_by_id("place_search_1").clear()
        driver.find_element_by_id("place_search_1").send_keys("within 10km from 50,15\n")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[data-pk="62"]')))
        driver.find_element_by_css_selector("#right_panel span.title").click()
        driver.find_element_by_css_selector("#places_list_wrapper > #groups_list > li > div.map_btn.small_btn").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.leaflet-popup')))
        driver.find_element_by_xpath("//div[@id='map']/div[2]/div[2]/div").click()
        
        driver.find_element_by_id("place_search_1").clear()
        driver.find_element_by_id("place_search_1").send_keys("vsera\n")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[data-pk="189"]')))
        driver.find_element_by_css_selector("#right_panel span.title").click()
        driver.find_element_by_css_selector("#places_list_wrapper > #groups_list > li > div.map_btn.small_btn").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.leaflet-popup')))
        driver.find_element_by_xpath("//div[@id='map']/div[2]/div[2]/div").click()
        
        driver.find_element_by_id("place_search_1").clear()
        driver.find_element_by_id("place_search_1").send_keys("")
        driver.find_element_by_id("place_search_btn").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'a.next')))
        driver.find_element_by_id("logo").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.banner1')))
        
    def login(self, user, password):
        driver = self.driver
        driver.get(self.base_url + "/accounts/login/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys(user)
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys(password)
        driver.find_element_by_css_selector("input[type=\"submit\"]").click()
        
    def logout(self):
        self.driver.find_element_by_id("logout-btn").click()
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        if START_SERVERS:
            self.process_server.kill()
            self.web_server.kill()
        self.assertEqual([], self.verificationErrors)
        
def report_result(count, case, time):
    remote.send_msg(socket, proc_id, 'measurement', (count, case, time))
    
CYCLES=1000
CASES='all'
START_SERVERS=False
BASE_URL="http://localhost:8001"
DRIVER='firefox'
ADDR='tcp://127.0.0.1:10101'

import argparse
if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument('--cycles',type=int, help="Number of iterations")
    p.add_argument('--cases', help='Test cases to run - either all or list of numbers like 1,2,3')
    p.add_argument('--start-servers', action="store_true", help="start servers (web and task server)")
    p.add_argument('--base-url', help="base url for tests")
    p.add_argument('--driver',   choices=('chrome', 'firefox'), help='selenium web driver ')
    p.add_argument('--recorder-address', help="Remote results recorder")
    args=p.parse_args()
    CYCLES=args.cycles or CYCLES
    CASES=args.cases or CASES
    START_SERVERS=args.start_servers or START_SERVERS
    BASE_URL=args.base_url or BASE_URL
    DRIVER=args.driver or DRIVER
    ADDR=args.recorder_address or ADDR
    
    remote.init()
    ctx=remote.context()
    socket=ctx.socket(zmq.PUB)
    socket.connect(ADDR)
    proc_id=gethostname() +'-'+ str(os.getpid())
    def finish(sig, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, finish )
    time.sleep(0.1)
    remote.send_msg(socket, proc_id, 'start', (time.time(),))
    try:
        unittest.main(argv=sys.argv[:1])
    finally:
        remote.send_msg(socket, proc_id, 'stop', (time.time(),))
    