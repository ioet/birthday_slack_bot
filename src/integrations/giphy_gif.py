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
    preview_renditions: tuple = (
        'fixed_height_small_still',
        'fixed_width_small_still',
        'preview_webp',
        'preview_gif',
        'fixed_height_small',
        'fixed_width_small',
    )

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
    def _select_preview_image_url(cls, images: dict, fallback_url: str = '') -> str:
        candidates = []
        for rendition in cls.preview_renditions:
            info = images.get(rendition) or {}
            url = info.get('url')
            if not url:
                continue
            size = info.get('size')
            try:
                size_value = int(size) if size is not None else 10 ** 12
            except (TypeError, ValueError):
                size_value = 10 ** 12
            candidates.append((size_value, url))

        if candidates:
            candidates.sort(key=lambda item: item[0])
            return candidates[0][1]
        return fallback_url or cls.failback_gif

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
        url = cls._select_image_url(images)
        return {
            'description': selected_gif.get('title', ''),
            'url': url,
            'preview_url': cls._select_preview_image_url(images, fallback_url=url),
        }
