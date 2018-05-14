# from django.test import TestCase

import pandas as pd
# Create your tests here.

df1 = pd.DataFrame({'A': ['A0', 'A1', 'A2', 'A3'],
                    'B': ['B0', 'B1', 'B2', 'B3'],
                    'C': ['C0', 'C1', 'C2', 'C3'],
                    'D': ['D0', 'D1', 'D2', 'D3']})
df1["index"] = [0, 1, 2, 3]
df1 = df1.set_index("index")

df4 = pd.DataFrame({'G': ['B2', 'B3', 'B6', 'B7'],
                    'T': ['D2', 'D3', 'D6', 'D7'],
                    'F': ['F2', 'F3', 'F6', 'F7']})
df4["index"] = [2.5, 1, 6, 7]
df4 = df4.set_index("index")


# print(df1)
#
# print("##########")
#
# print(df4)
#
# print("##########")
#
# print(df1.join(df4, how="outer"))

################
################

df1 = pd.DataFrame([[1, 3], [2, 4]], columns=['A', 'B'])

df2 = pd.DataFrame([[1, 5], [1, 6]], columns=['A', 'C'])

df = df1.merge(df2, how='outer')

print(df1)
print()
print(df2)
print()
print(df)


################
