
import requests
from typing import Optional


class RestClient:

    def __init__(self, base_url: str, api_token: Optional[str] = None, is_bearer: bool = False, is_basic_auth: bool = False) -> 'RestClient':
        self.base_url = base_url.rstrip('/')
        self.headers = {'Authorization': f'Bearer {api_token}'} if api_token and is_bearer else {}
        self.basic_auth = (api_token, '') if api_token and is_basic_auth else None

    def get(self, additional_url: str = '', query_params: Optional[dict] = None) -> requests.Response:
        return requests.get(f'{self.base_url}/{additional_url}', params=query_params or {}, headers=self.headers, auth=self.basic_auth)

    def post(self, additional_url: str = '',  payload: Optional[dict] = None, query_params: Optional[dict] = None,) -> requests.Response:
        return requests.post(f'{self.base_url}/{additional_url}', params=query_params or {}, json=payload, headers=self.headers, auth=self.basic_auth)
