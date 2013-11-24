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

class LoginLogOut(unittest.TestCase):
    def setUp(self):
        manage=os.path.join(os.path.split(__file__)[0], '../../../manage.py')
        self.web_server=subprocess.Popen(['python', manage,  'runserver_socketio', 'localhost:8001'], shell=False)
        self.process_server=subprocess.Popen(['python', manage,  'process_server'], shell=False)
        
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8001"
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_interaction(self):
        self.login('admin', 'admin')
        for i in range(1000):
            start=time.time()
            self.case1()
            dur=time.time()-start
            print '%d - %f' %(i, dur)
        
        self.logout()
        
    def case1(self):
        driver=self.driver
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[2]/span").click()
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[2]/div[3]/div/div/div[2]").click()
        driver.find_element_by_xpath("//ul[@id='groups_list']/li[7]/div").click()
       
        driver.find_element_by_link_text(u"×").click()

        driver.find_element_by_xpath(u"//img[@title='Bobrovská Martina,  Centrum léčebné rehabilitace']").click()
        driver.find_element_by_link_text(u"×").click()
        driver.find_element_by_xpath("//div[@id='map']/div[2]/div[2]/div").click()
        driver.find_element_by_id("place_search_3").clear()
        driver.find_element_by_id("place_search_3").send_keys("chrb")
        driver.find_element_by_css_selector("#places_list_wrapper > #groups_list > li > div.edit_btn.small_btn").click()
        driver.find_element_by_css_selector("input.cancel_btn").click()
        driver.find_element_by_id("logo").click()
        
    def login(self, user, password):
        driver = self.driver
        driver.get(self.base_url + "/mp/")
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
        self.process_server.kill()
        self.web_server.kill()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()