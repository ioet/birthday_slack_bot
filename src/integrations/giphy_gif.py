from random import choice

from ..clients import RestClient
from ..config import EnvManager


class GiphyGifIntegration:
    client = RestClient('https://api.giphy.com/v1/gifs')
    api_key: str = EnvManager.GIPHY_API_KEY
    failback_gif: str = ''

    @classmethod
    async def get_random_gif(cls, search_criteria: str, limit: int = 2) -> dict:
        response = await cls.client.get('search', query_params={
            'q': search_criteria,
            'api_key': cls.api_key,
            'limit': limit,
        })
        options = response.json().get('data', [])
        selected_gif = choice(options)
        images = selected_gif.get('images', {})
        url = cls.failback_gif if not images else images.get('fixed_height_small', {}).get('url')
        return {
            'description': selected_gif.get('title', ''),
            'url': url,
        }
