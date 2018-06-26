import json

s = list()
file_path = "C:/Users/Daniel/Desktop/mill/finance_project/finance/finance/media/crypto/prices/20180622.json"
tupli = []
with open(file_path, "r") as file:
    data = json.load(file)
    i = 0
    for entry in data:
    	i += 1
    	if i>70:
    		break
    	text = "(\"{}\", \"{}\")".format(entry["symbol"], entry["name"])
    	tupli.append((entry["symbol"], entry["name"]))
    	s.append(text)
haha = str(s)
ss = list()
for a in haha:
	if a == "'":
		continue
	ss.append(a)
# print("".join(ss).replace("[", "").replace("]", ""))

tupli = tuple(tupli)
print(tupli)
for t in tupli:
	print(t[0])
