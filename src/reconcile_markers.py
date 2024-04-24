import json
import os
from pathlib import Path
import pandas as pd
from wikibaseintegrator import WikibaseIntegrator
from login import USER, PASS

from wikibaseintegrator import wbi_login

login_instance = wbi_login.Clientlogin(user=USER, password=PASS)
wbi = WikibaseIntegrator(login=login_instance)

HERE = Path(__file__).parent.resolve()
DATA = HERE.parent.joinpath("data").resolve()
DICTS = HERE.parent.joinpath("dictionaries").resolve()

os.system(
    "wget -O data/cell_classes.xlsx"
    "https://docs.google.com/spreadsheets/d/e/"
    r"2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-"
    r"YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub\?output\=xlsx"
)

cell_markers = pd.read_excel("data/cell_classes.xlsx", sheet_name="cell markers")

def split_markers(marker_string):
    marker_string = marker_string.replace("+", " ")
    marker_string = marker_string.replace("(", " ")
    marker_string = marker_string.replace(")", " ")
    marker_string = marker_string.replace(")", " ")
    sep_markers = marker_string.split(",")
    sep_markers = [s.replace("and", "").strip() for s in sep_markers]
    return sep_markers


cell_type_dict = json.loads(DICTS.joinpath("celltypes_dict.json").read_text())

def travel_gene_dict(gene_name, species):

    path = f"dictionaries/{species}_gene.json"
    with open(path, "r") as f:
        gene_dict = json.loads(f.read())

    for gene in gene_dict:
        if gene == gene_name:
            return gene_dict[gene]

from wikibaseintegrator import datatypes


for index, row in cell_markers.iterrows():

    marker_labels = row["marker "]
    print(marker_labels)

    marker_list = split_markers(marker_labels)
    data_for_item = []


    references = [
        [
    datatypes.MonolingualText(text=row["stated as"], prop_nr="P1683",language="en"),
        datatypes.Item(value=row["stated in"], prop_nr="P248")]
        ]

    label = row["cell class"]
    print(f"Running code for {label} ")

    entity = wbi.item.get(cell_type_dict[row["cell class"]])

    for marker in marker_list:
        print(marker)
        if "human" in label:
            gene_qid = travel_gene_dict(marker, "human")
        elif "mouse" in label:
            gene_qid = travel_gene_dict(marker, "human")
        else:
            continue
        new_claim = datatypes.Item(prop_nr='P8872', value=gene_qid, references=references)
        print(gene_qid)
        print(entity.claims)
        entity.claims.add(new_claim)
        print(entity.claims)

    entity.write()