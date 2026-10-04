import pickle

resp = []

for questao in range(1, 11):
    for alternativa in ["A", "B", "C", "D", "E"]:
        resp.append(f"{questao}-{alternativa}")

with open("resp.pkl", "wb") as arquivo:
    pickle.dump(resp, arquivo)

print(resp)
print("Quantidade:", len(resp))