"""Questrade test module
"""
from unittest import mock
import pytest
from qtrade import Questrade

TOKEN_URL = 'https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token='

VALID_ACCESS_TOKEN = {'access_token': 'hunter2',
                      'api_server': "https://questrade.api",
                      'expires_in': 1234,
                      'refresh_token': 'hunter2',
                      'token_type': 'Bearer'}

INVALID_ACCESS_TOKEN = {'access_token': 'hunter3',
                        'api_server': 'https://questrade.api',
                        'expires_in': 1234,
                        'refresh_token': 'hunter3'}
ACCOUNT_RESPONSE = {'accounts': [{'number': 123}, {'number': 456}]}
POSITION_RESPONSE = {'positions': [{'averageEntryPrice': 1000,
                                    'closedPnl': 0,
                                    'closedQuantity': 0,
                                    'currentMarketValue': 3120,
                                    'currentPrice': 1040,
                                    'isRealTime': False,
                                    'isUnderReorg': False,
                                    'openPnl': 120,
                                    'openQuantity': 3,
                                    'symbol': 'XYZ',
                                    'symbolId': 1234567,
                                    'totalCost': 3000},
                                   {'averageEntryPrice': 500,
                                    'closedPnl': 0,
                                    'closedQuantity': 0,
                                    'currentMarketValue': 4000,
                                    'currentPrice': 1000,
                                    'isRealTime': False,
                                    'isUnderReorg': False,
                                    'openPnl': 2000,
                                    'openQuantity': 4,
                                    'symbol': 'ABC',
                                    'symbolId': 7654321,
                                    'totalCost': 2000}]}


ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: www.api_url.com
expires_in: 1234
refresh_token: hunter2
token_type: Bearer
"""

INCOMPLETE_ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: www.api_url.com
expires_in: 1234
"""

# taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
# Since a lot of the methods in the Questrade class use `requests.get` and get the json data,
# it makes sense to wrap this in a class
class MockResponse:
    """Class that includes json data and status code for request get results
    """
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Method to return mocked json data
        """
        return self.json_data

    def raise_for_status(self):
        """Method to raise Exceptions for certain returned statuses
        """
        http_error_msg = ''
        if 400 <= self.status_code < 500:
            http_error_msg = '%s Client Error' % (self.status_code)

        elif 500 <= self.status_code < 600:
            http_error_msg = '%s Server Error' % (self.status_code)

        if http_error_msg:
            raise Exception(http_error_msg)


def mocked_access_token_requests_get(*args, **kwargs):
    """mocking access token requests get method
    """
    if args[0] == TOKEN_URL + 'hunter2':
        return MockResponse(VALID_ACCESS_TOKEN, 200)
    elif args[0] == TOKEN_URL + 'hunter3':
        return MockResponse(INVALID_ACCESS_TOKEN, 200)
    else:
        return MockResponse(None, 404)

def mocked_acct_id_get(*args, **kwargs):
    """mocking acct_id requests get
    """
    if args[0] == 'www.api_url.com/v1/accounts':
        return MockResponse(ACCOUNT_RESPONSE, 200)
    else:
        return MockResponse(None, 404)

def mocked_positions_get(*args, **kwargs):
    """mocking acct_id requests get
    """
    if args[0] == 'www.api_url.com/v1/accounts/123/positions':
        return MockResponse(POSITION_RESPONSE, 200)
    else:
        return MockResponse(None, 404)


@mock.patch('qtrade.questrade.requests.get', side_effect=mocked_access_token_requests_get)
def test_get_access_token(mock_get):
    """This function tests the get access token method.
    """
    qtrade = Questrade(access_code='hunter2')
    assert set(qtrade.access_token.keys()) == set(['access_token', 'api_server', 'expires_in',
                                                   'refresh_token', 'token_type'])
    with pytest.raises(Exception) as e_info:
        _ = Questrade(access_code='hunter3')
        assert str(e_info.value) == 'Token type was not provided.'

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
def test_init_via_yaml():
    """This function tests when the class is initiated via yaml file.
    """
    qtrade = Questrade(token_yaml='access_token.yml')
    assert set(qtrade.access_token.keys()) == set(['access_token', 'api_server', 'expires_in',
                                                   'refresh_token', 'token_type'])
    assert qtrade.access_token['access_token'] == 'hunter2'
    assert qtrade.access_token['api_server'] == 'www.api_url.com'
    assert qtrade.access_token['expires_in'] == 1234
    assert qtrade.access_token['refresh_token'] == 'hunter2'
    assert qtrade.access_token['token_type'] == 'Bearer'

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
def test_init_via_incomplete_yaml():
    """This function tests when the class is initiated via incomplete yaml file.
    """
    with pytest.raises(Exception) as e_info:
        _ = Questrade(token_yaml='access_token.yml')
        assert str(e_info.value) == 'Refresh token was not provided.'

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch('qtrade.questrade.requests.get', side_effect=mocked_access_token_requests_get)
def test_refresh_token_yaml(mock_get):
    """This function tests the refresh token method.
    """
    qtrade = Questrade(token_yaml='access_token.yml')
    qtrade.refresh_access_token()
    assert set(qtrade.access_token.keys()) == set(['access_token', 'api_server', 'expires_in',
                                                   'refresh_token', 'token_type'])
    assert qtrade.access_token['api_server'] == 'https://questrade.api'

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch('qtrade.questrade.requests.get', side_effect=mocked_access_token_requests_get)
def test_refresh_token_non_yaml(mock_get):
    """This function tests the refresh token method.
    """
    qtrade = Questrade(token_yaml='access_token.yml')
    qtrade.refresh_access_token(from_yaml=False)
    assert set(qtrade.access_token.keys()) == set(['access_token', 'api_server', 'expires_in',
                                                   'refresh_token', 'token_type'])
    assert qtrade.access_token['api_server'] == 'https://questrade.api'

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch('qtrade.questrade.requests.get', side_effect=mocked_acct_id_get)
def test_get_account_id(mock_get):
    """This function tests the account ID function.
    """
    qtrade = Questrade(token_yaml='access_token.yml')
    acct_id = qtrade.get_account_id()
    assert acct_id == [123, 456]

@mock.patch('builtins.open', mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch('qtrade.questrade.requests.get', side_effect=mocked_positions_get)
def test_get_positions(mock_get):
    """This function tests the get account positions method.
    """
    qtrade = Questrade(token_yaml='access_token.yml')
    positions = qtrade.get_account_positions(123)
    assert positions[0]['symbol'] == 'XYZ'
    assert positions[1]['symbol'] == 'ABC'
    assert positions[0]['currentMarketValue'] == 3120
    assert positions[1]['currentMarketValue'] == 4000
    assert len(positions) == 2
    assert len(positions[0]) == 12
    assert len(positions[1]) == 12