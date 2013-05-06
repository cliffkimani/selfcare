"""
selfcare.py
Simple tool for scraping and parsing airtime / data bundle data
from selfcare.safaricom.co.ke

Please understand that use of this tool is very likely against
the terms of service for use of Safaricom products and services.

You'll of course need a registered account with one or more SIMs
in Safaricom selfcare for this to work.

Handle with care.

You'll need:
BeutifulSoup - http://www.crummy.com/software/BeautifulSoup/
"""

__author__ = "Jeremy Gordon (onejgordon@gmail.com)"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 20013 Jeremy Gordon"
__license__ = "New-style BSD"

from BeautifulSoup import BeautifulSoup
import logging
import mechanize
import re

sims = []

class SIM(object):
	def __init__(self, phone, airtime=None, data=None):
		self.phone = phone
		self.airtime = airtime
		self.data = data

	def __str__(self):
		return "SIM [ %s ] Airtime: %s kes, Data: %s kb" % (self.phone, self.airtime, self.data)

class Scraper(object):
    BASE = "http://selfcare.safaricom.co.ke/Home.action"
    # Fill these values with your Safaricom account information
    UNAME = ""
    PASSWORD = ""
    # List of full international sims to check balance of
    sims = ["254700000000"]

    def __init__(self):
        self.br = mechanize.Browser()
        self.br.set_handle_refresh(False)
        self.br.set_handle_robots(False)

    def run(self):
        response1 = self.br.open(self.BASE, timeout=10)
        self._got_page(response1)
        self.br.select_form(name='LoginPanelAction')
        self.br['login'] = self.UNAME
        self.br['password'] = self.PASSWORD
        response2 = self.br.submit()
        self._got_page(response2)
        try:
	        response3 = self.br.follow_link(text_regex=r"Balance", nr=0)
        except Exception, e:
        	logging.error("Couldn't find 'Balance' link - maybe we didn't login?")
        else:
	        self._got_page(response3)
	        SIM_CHOOSER_FORM = "BalanceInquiries"
	        SIM_CHOOSER_DROPDOWN = "selectedAccountDropdownFieldValue"
	        self.br.select_form(name=SIM_CHOOSER_FORM)
	        control = self.br.form.find_control(SIM_CHOOSER_DROPDOWN)
	        if control.type == "select":
	            for i, item in enumerate(control.items):
	                label = item.get_labels()[0]
	                if label:
		                mtch = re.match(r'.*? \((\d{9})\)$', str(label.text))
		                if mtch:
		                    phone = '254' + mtch.group(1)
		                    if phone in self.sims:
								val = item.attrs['value']
								self.br.select_form(name=SIM_CHOOSER_FORM)
								self.br[control.name] = [val] # Set select to found option
								response4 = self.br.submit()
								self._scrape(response4, phone)
								self.br.back()
				logging.debug("Done!")
	        else:
	            self._problem("Couldn't find phone select")

    def _scrape(self, resp, sim):
		logging.debug("Scraping page: %s" % self.br.title())
		html = resp.read()
		soup = BeautifulSoup(html)
		table = soup.find('table', {'class':'dataTable'})
		airtime = data = None
		for row in table.findAll('tr')[1:]:
			col = row.findAll('td')
			description = col[0].string
			balance = col[1].string
			units = col[2].string
			expiry = col[3].string
			clean_units = units.upper().strip()
			if clean_units == "KSH":
				airtime = int(float(balance.strip()))
			elif clean_units == "KBYTES" and description == "Daily Bundle GPRS":
				ndata = int(float(balance.strip()))
				if data is None or ndata < ndata:
					# Replace previous with new (it's lower)
					data = ndata
		s = SIM(sim, airtime=airtime, data=data)
		sims.append(s)

    def _problem(s):
        logging.error("Problem mechanizing! Details: %s" % s)

    def _got_page(self, resp):
        s = "Got [ %s ] at %s" % (self.br.title(), resp.geturl())
        logging.debug(s)


if __name__ == '__main__':
	scraper = Scraper()
	scraper.run()
	for sim in sims:
		print str(sim)
