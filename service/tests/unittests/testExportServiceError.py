from flask_testing import TestCase
import unittest
import service.app as app
import json

class TestExportsError(TestCase):
    def create_app(self):
        app_ = app.create_app()
        return app_

    def test_noPayload(self):
        """
        Ensure that if no payload is passed in, returns 400
        """
        for route in ['//', '/bibtex', '/fielded', '/xml' , '/csl', '/custom']:
            r = self.client.post(route)
            status = r.status_code
            response = r.data
            self.assertEqual(status, 400)
            self.assertEqual(response, 'error: no information received')

    def test_noPayloadParam(self):
        """
        Ensure that if payload without all the needed params is passed in, returns 400
        """
        for route in ['//', '/bibtex', '/fielded', '/xml' , '/csl', '/custom']:
            r = self.client.post(route, data=json.dumps('missingParamsPayload'))
            status = r.status_code
            response = r.data

            self.assertEqual(status, 400)
            self.assertEqual(response, 'error: no bibcodes found in payload (parameter name is "bibcode")')

    def test_missingPayloadParam(self):
        """
        Ensure that all of the payload params were passed in, otherwise returns 400
        """
        payload = {'bibcode': '', 'style': '', 'format': ''}
        for route in ['//', '/bibtex', '/fielded', '/xml', '/csl', '/custom']:
            r = self.client.post(route, data=json.dumps(payload))
            status = r.status_code
            response = r.data

            self.assertEqual(status, 400)
            self.assertEqual(response, 'error: not all the needed information received')

    def test_nonExistStyle(self):
        """
        Ensure that if payload contains the supported styles for each endpoints otherwise returns 503
        """
        payload = {'bibcode': '1989ApJ...342L..71R', 'style': 'nonExsistingStyle', 'format': 'nonEsistingFormat'}
        endPoint = {
                '/bibtex':'error: unrecognizable style (supprted styles are: BibTex, BibTexAbs)',
                '/fielded':'error: unrecognizable style (supprted styles are: ADS, EndNote, ProCite, Refman, RefWorks, MEDLARS)',
                '/xml':'error: unrecognizable style (supprted styles are: Dublin, Reference, ReferenceAbs)',
                '/csl':'error: unrecognizable style (supprted formats are: aastex, icarus, mnras, soph, aspc, apsj, aasj)'}
        for key in endPoint:
            r = self.client.post(key, data=json.dumps(payload))
            status = r.status_code
            response = r.data
            self.assertEqual(status, 503)
            self.assertEqual(response, endPoint[key])

    def test_nonExistFormat(self):
        """
        Ensure that if payload contains the supported styles for each endpoints otherwise returns 503
        """
        payload = {'bibcode': '1989ApJ...342L..71R', 'style': 'aastex', 'format': 'nonEsistingFormat'}
        endPoint = {
                '/csl':'error: unrecognizable format (supprted formats are: unicode=1, html=2, latex=3)'}
        for key in endPoint:
            r = self.client.post(key, data=json.dumps(payload))
            status = r.status_code
            response = r.data
            self.assertEqual(status, 503)
            self.assertEqual(response, endPoint[key])

if __name__ == "__main__":
    unittest.main()
