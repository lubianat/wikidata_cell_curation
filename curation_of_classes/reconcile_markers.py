import os
import pandas as pd
from dicts import *
import re
import pickle
import time
from wikidataintegrator import wdi_login, wdi_core
import getpass
import json

os.system(
    "wget -O cell_classes.xlsx https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub\?output\=xlsx"
)

cell_markers = pd.read_excel("cell_classes.xlsx", sheet_name="cell markers")


def split_markers(marker_string):

    marker_string = marker_string.replace("+", " ")
    marker_string = marker_string.replace("(", " ")
    marker_string = marker_string.replace(")", " ")
    marker_string = marker_string.replace(")", " ")

    sep_markers = marker_string.split(",")
    sep_markers = [s.replace("and", "").strip() for s in sep_markers]
    return sep_markers


with open("celltypes_dict.pickle", "rb") as handle:
    subclass_dict = pickle.load(handle)

pwd = getpass.getpass()
login_instance = wdi_login.WDLogin(user="TiagoLubiana", pwd=pwd)


def travel_gene_dict(gene_name, species):

    path = f"dictionaries/{species}_gene.json"
    with open(path, "r") as f:
        gene_dict = json.loads(f.read())

    for gene in gene_dict:
        if gene == gene_name:
            return gene_dict[gene]


try:
    for index, row in cell_markers.iterrows():

        marker_labels = row["marker"]
        print(marker_labels)

        marker_list = split_markers(marker_labels)
        data_for_item = []
        stated_in_full_reference = wdi_core.WDItemID(
            value=row["stated in"], prop_nr="P248", is_reference=True
        )
        references = [[stated_in_full_reference]]

        label = row["label"]
        print(f"Running code for {label} ")

        for marker in marker_list:
            if "human" in label:
                ## Look for human gene ID
                qid = travel_gene_dict(marker, "human")
                print(qid)

            elif "mouse" in label:
                ## Look for mouse gene ID
                pass

            elif "zebrafish" in label:
                ## Look for zebrafish gene id
                pass
            else:
                description = "cell type"
except:
    print("oops")
