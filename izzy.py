#!/usr/bin/env python

import settings
from lib.izzybot import IzzyBot


if __name__ == "__main__":
    izzy = IzzyBot(settings)
    izzy.run()
