from random import choice

from ..clients import RestClient
from ..config import EnvManager


class TenorGifIntegration:
    client = RestClient('https://g.tenor.com/v1')
    api_key: str = EnvManager.TENOR_API_KEY
    failback_gif: str = ''

    @classmethod
    def get_random_gif(cls, search_criteria: str, limit: int = 2) -> dict:
        response = cls.client.get('search', query_params={'q': search_criteria, 'key': cls.api_key, 'limit': limit})
        options = response.json().get('results', [])
        selected_gif = choice(options)
        selected_gif_media = selected_gif.get('media', [])
        url = cls.failback_gif if not selected_gif_media else selected_gif_media.pop().get('tinygif', {}).get('url')
        return {
            'description': selected_gif.get('content_description'),
            'url': url,
        }
