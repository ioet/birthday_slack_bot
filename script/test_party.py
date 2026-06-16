#!/usr/bin/env python3
"""Run the party bot end-to-end: Bamboo, Giphy, Slack API, and Slack webhook."""

import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_dotenv() -> None:
    env_file = ROOT / '.env'
    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().split('#', 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()

from main_party import main

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def run() -> None:
    logger.info('Running party bot (birthdays + anniversaries)...')
    result = await main(None, None)
    logger.info('Done: %s', result.get('message'))


if __name__ == '__main__':
    asyncio.run(run())
