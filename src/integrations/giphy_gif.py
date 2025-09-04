from random import choice
from src.clients.rest import RestClient
from src.config import EnvManager


class TenorGifIntegration:
    client = RestClient('https://api.giphy.com/v1/gifs/')
    failback_gif: str = ''

    @classmethod
    async def get_random_gif(cls, search_criteria: str) -> dict:
        response = await cls.client.get('search', query_params={'q': search_criteria, 'api_key': EnvManager.GIPHY_API_KEY})
        data = response.json()['data']
        selected_gif = choice(data)
        selected_gif_url = selected_gif.get('images', {}).get('original', {}).get('url', {})
        return {
            'description': selected_gif.get('title'),
            'url': selected_gif_url,
        }
