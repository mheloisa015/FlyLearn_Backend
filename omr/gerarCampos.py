"""Gera campos_10.pkl e campos_20.pkl (quadrados de leitura de cada bolha) a partir do omr_config.py.

O app_web.py já calcula os campos sozinho (omr_config.campos(n)); este script só existe para
quem quiser inspecionar/regenerar os .pkl. Rode dentro da pasta omr/:  python gerarCampos.py
"""
import pickle

from omr_config import QUANTIDADES, campos

for n in QUANTIDADES:
    lista = campos(n)
    with open(f"campos_{n}.pkl", "wb") as arquivo:
        pickle.dump(lista, arquivo)
    print(f"campos_{n}.pkl criado! Quantidade:", len(lista))