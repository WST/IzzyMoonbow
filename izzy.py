#!/usr/bin/env python3

import settings
from lib.izzybot import IzzyBot


if __name__ == "__main__":
    izzy = IzzyBot(settings)
    izzy.run()
