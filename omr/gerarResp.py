"""Gera resp_10.pkl e resp_20.pkl (rótulos "questão-alternativa" na ordem das bolhas)."""
import pickle

from omr_config import QUANTIDADES

for n in QUANTIDADES:
    resp = [f"{questao}-{alt}" for questao in range(1, n + 1) for alt in "ABCDE"]
    with open(f"resp_{n}.pkl", "wb") as arquivo:
        pickle.dump(resp, arquivo)
    print(f"resp_{n}.pkl criado! Quantidade:", len(resp))