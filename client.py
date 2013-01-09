from bs4 import BeautifulSoup
from urllib2 import urlopen, Request, HTTPError


class CWGCClient():
    '''
    Basic scraper/client for extracting structured data from the Commonwealth
    War Graves Commission database.

    USAGE:

    import client
    cwgc = client.CWGCClient()
    details = cwgc.get_details(url)

    'url' is the url of an individual entry for a person in the CWGC database.

    SAMPLE RESULTS:

    {
        'additional_information': u'Son of Edward and Alice Crisford, of 104, Glover St., Mosman, New South Wales. Born at Gordon, New South Wales.',
        'age': u'24',
        'cemetery': {
            'country': u'France',
            'locality': u'Pas de Calais',
            'name': u'QUEANT ROAD CEMETERY, BUISSY',
            'url': 'http://www.cwgc.org/find-a-cemetery/cemetery/32500/QUEANT ROAD CEMETERY, BUISSY'},
        'date_of_death': u'23/04/1917',
        'grave_reference': u'Sp. Mem. B. 3.',
        'name': u'CRISFORD, WILFRED REGINALD EDGAR',
        'rank': u'Gunner',
        'service': u'Australian Field Artillery',
        'service_no': u'9389',
        'unit': u'5th Bde.',
        'url': 'http://www.cwgc.org/find-war-dead/casualty/313405/CRISFORD,%20WILFRED%20REGINALD%20EDGAR'
    }
    '''

    FIELDS = [

                'Rank:',
                'Service No:',
                'Date of Death:',
                'Age:',
                'Grave Reference',
            ]

    CWGC_URL = 'http://www.cwgc.org'

    def _get_field_value(self, soup, field):
        ''' Get the value of a field. '''
        try:
            value = soup.find('dt', text=field).find_next_sibling('dd').string.strip()
        except AttributeError:
            value = None
        return value

    def _get_name(self, soup):
        ''' Get the person's name. '''
        return soup.h2.string.strip()

    def _get_additional_info(self, soup):
        ''' Get the additional information note. '''
        try:
            info = soup.find('h3', text='Additional Information:').find_next_sibling('p').string.strip()
        except AttributeError:
            info = None
        return info

    def _get_service(self, soup):
        ''' Get service and unit details. '''
        service = self._get_field_value(soup, 'Regiment/Service:')
        print soup.find_all('dt')
        unit = self._get_field_value(soup, '\xc2\xa0')
        return {'service': service, 'unit': unit}

    def _process_fieldname(self, field):
        ''' Slugify fieldnames '''
        return field.lower().replace(' ', '_').replace(':', '')

    # Uncomment the next line to retry in the case of a timeout error.
    #@retry(ServerError, tries=10, delay=1)
    def _get_url(self, url):
        ''' Try to retrieve the supplied url.'''
        req = Request(url)
        try:
            response = urlopen(req)
        except HTTPError as e:
            if e.code == 503 or e.code == 504:
                raise ServerError("The server didn't respond")
            else:
                raise
        else:
            return response

    def get_details(self, url):
        ''' Return all the extracted details for the supplied url.'''
        response = self._get_url(url)
        soup = BeautifulSoup(response.read(), 'lxml')
        details = {}
        details['url'] = url
        details['name'] = self._get_name(soup)
        for field in self.FIELDS:
            fieldname = self._process_fieldname(field)
            details[fieldname] = self._get_field_value(soup, field)
        details['additional_information'] = self._get_additional_info(soup)
        details.update(self._get_service(soup))
        details['cemetery'] = self._get_cemetery(soup)
        return details

    def _get_cemetery(self, soup):
        ''' Get the basic cemetery details. '''
        cemetery = {}
        try:
            cemetery['name'] = soup.find('div', 'greyBox').h2.string.strip()
            cemetery['url'] = '{}{}'.format(
                                            self.CWGC_URL,
                                            soup.find('p', 'readMore').a['href']
                                            )
        except AttributeError:
            cemetery['name'] = None
        cemetery['country'] = self._get_field_value(soup, 'Country:')
        cemetery['locality'] = self._get_field_value(soup, 'Locality:')
        return cemetery


class ServerError(Exception):
    pass
