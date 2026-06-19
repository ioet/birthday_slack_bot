from random import choice

from ..clients import RestClient
from ..config import EnvManager


class GiphyGifIntegration:
    client = RestClient('https://api.giphy.com/v1/gifs')
    api_key: str = EnvManager.GIPHY_API_KEY
    failback_gif: str = ''
    min_width: int = 200
    max_width: int = 400
    fallback_renditions: tuple = ('fixed_width', 'fixed_height', 'downsized_medium', 'downsized')

    @classmethod
    def _select_image_url(cls, images: dict) -> str:
        if not images:
            return cls.failback_gif

        in_range = []
        for image in images.values():
            url = image.get('url')
            width = image.get('width')
            if not url or width is None:
                continue
            try:
                width = int(width)
            except (TypeError, ValueError):
                continue
            if cls.min_width <= width <= cls.max_width:
                in_range.append((width, url))

        if in_range:
            target_width = (cls.min_width + cls.max_width) // 2
            in_range.sort(key=lambda item: abs(item[0] - target_width))
            return in_range[0][1]

        for rendition in cls.fallback_renditions:
            url = images.get(rendition, {}).get('url')
            if url:
                return url

        return images.get('fixed_height_small', {}).get('url') or cls.failback_gif

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
        return {
            'description': selected_gif.get('title', ''),
            'url': cls._select_image_url(images),
        }
