"""Helper class to connect Nimbus service"""
import logging
from decorators import singleton
from deploy_board.settings import NIMBUS_SERVICE_URL, NIMBUS_SERVICE_VERSION, TELETRAAN_PROJECT_URL_FORMAT
from exceptions import NotAuthorizedException, TeletraanException, FailedAuthenticationException
import requests
requests.packages.urllib3.disable_warnings()

log = logging.getLogger(__name__)

@singleton
class NimbusClient(object):
    def handle_response(self, response):
        if response.status_code == 404:
            log.error("Resource not found. Nimbus API response - %s" % response.content)
            return None

        if response.status_code == 409:
            log.error("Resource already exists. Nimbus API response - %s" % response.content)
            raise TeletraanException('Resource conflict - Nimbus already has an Identifier for your proposed new stage. ')

        if 400 <= response.status_code < 600:
            log.error("Nimbus API Error %s, %s" % (response.content, response.status_code))
            raise TeletraanException(
                "Teletraan failed to successfully call Nimbus. Contact your friendly Teletraan owners for assistance. Hint: %s, %s" % (response.status_code, response.content)
            )

        if response.status_code == 200 or response.status_code == 201:
            return response.json()

        return None

    def get_one_identifier(self, name, token=None):
        headers = {}
        if token:
            headers['Authorization'] = 'token %s' % token

        log.error("CALLING %s TO GET IDENTIFIER" % NIMBUS_SERVICE_URL)
        response = requests.get('{}/api/{}/identifiers/{}'.format(NIMBUS_SERVICE_URL, NIMBUS_SERVICE_VERSION, name),
                                headers=headers)
        return self.handle_response(response)

    def create_one_identifier(self, data, token=None):
        headers = {}
        if token:
            headers['Authorization'] = 'token %s' % token

        payload = {}
        payload['kind'] = 'Identifier'
        payload['apiVersion'] = 'v1'
        payload['platformName'] = 'teletraan'
        payload['projectName'] = data.get('projectName')

        for property in data['propertyList']['properties']:
            if property['propertyName'] == 'cellName':
                cellName = property['propertyValue']

        payload['spec'] = {
            'kind': 'EnvironmentSpec',
            'apiVersion': 'v1',
            'cellName': cellName,
            'envName': data.get('env_name'),
            'stageName': data.get('stage_name')
        }

        log.error("CALLING %s TO CREATE IDENTIFIER" % NIMBUS_SERVICE_URL)
        response = requests.post('{}/api/{}/identifiers'.format(NIMBUS_SERVICE_URL, NIMBUS_SERVICE_VERSION),
                                 json=payload,
                                 headers=headers)

        return self.handle_response(response)

    def delete_one_identifier(self, name, token=None):
        headers = {}
        if token:
            headers['Authorization'] = 'token %s' % token

        log.error("CALLING %s TO DELETE IDENTIFIER" % NIMBUS_SERVICE_URL)
        response = requests.delete('{}/api/{}/identifiers/{}'.format(NIMBUS_SERVICE_URL, NIMBUS_SERVICE_VERSION, name),
                                 headers=headers)
        return self.handle_response(response)

    def get_one_project_console_url(self, project_name):
        if not TELETRAAN_PROJECT_URL_FORMAT:
            return ""
        return TELETRAAN_PROJECT_URL_FORMAT.format(projectName=project_name)
