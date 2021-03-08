"""Helpers for fetching info from mypoll"""

import urllib.request
import json
import pandas as pd


URL = "https://comp550fa20.cs.unc.edu/mypoll/api/responses"

token = open("mytoken.txt", "r").read().strip()


def fetch_responses(key):
    """Return student responses for given key"""
    req = urllib.request.Request(f"{URL}/{key}", headers={"Authentication": token})
    rsp = urllib.request.urlopen(req)
    data = rsp.read()
    return json.loads(data.decode("utf-8"))


d = fetch_responses("hello")

# make it into a pandas dataframe
df = pd.DataFrame(d["result"])

# take their last submission
df = df.groupby("Onyen").last()

print(df.columns)
