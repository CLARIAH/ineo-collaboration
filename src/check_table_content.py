import os
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
import hashlib
import sqlite3
from datetime import datetime


if __name__ == '__main__':
    """
    """
    # init db and check if the table exists
    conn = sqlite3.connect("tools_metadata.db")
    # create a cursor
    c = conn.cursor()

    c.execute("SELECT * FROM tools_metadata;")

    for row in c.fetchall():
        print(row)


