import subprocess
import sys

import json

# args = sys.argv

# df = pd.read_csv(args[1])

# print(df.head())

# subprocess.call("echo args[0]")

f = open("config.json")
data = json.load(f)

print(data)