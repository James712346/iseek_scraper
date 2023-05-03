# Connect to a database, and insert 3 rows, with 3 columns
#
# This is the same as the above, but with a different database
#

import asyncio
import asyncpg
import logging
from time import sleep
from sys import stdout
from os import getenv
from models import Transit, Graphs
from scrapper import Iseek
from datetime import datetime
from typing import List, Dict, Union, Tuple, Optional
from pydantic import BaseModel

