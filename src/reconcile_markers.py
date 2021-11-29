import os
import pandas as pd
from dicts import *
import pickle
from wikidataintegrator import wdi_login, wdi_core
import getpass
import json

os.system(
    "wget -O data/cell_classes.xlsx https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub\?output\=xlsx"
)

cell_markers = pd.read_excel("data/cell_classes.xlsx", sheet_name="cell markers")

print(cell_markers.head())

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


for index, row in cell_markers.iterrows():

    marker_labels = row["marker "]
    print(marker_labels)

    marker_list = split_markers(marker_labels)
    data_for_item = []
    stated_in_full_reference = wdi_core.WDItemID(
        value=row["stated in"], prop_nr="P248", is_reference=True
    )

    stated_as_full_reference = wdi_core.WDString(
        value=row["stated as"], prop_nr="P1932", is_reference=True
    )
    references = [[stated_in_full_reference, stated_as_full_reference]]

    label = row["cell class"]
    print(f"Running code for {label} ")

    for marker in marker_list:
        if "human" in label:
            ## Look for human gene ID
            qid = travel_gene_dict(marker, "human")

            try:
                data_for_item.append(
                    wdi_core.WDItemID(
                        value=qid,
                        prop_nr="P8872",
                        references=references,
                    )
                )
                print(qid)
                cell_type_id = subclass_dict[row["cell class"]]
                print(cell_type_id)
                wd_item = wdi_core.WDItemEngine(
                    wd_item_id=cell_type_id, data=data_for_item, append_value=["P8872"]
                )
                print(wd_item)
                wd_item.write(login_instance)
            except:
                print(f"Failed for {marker}")

        elif "mouse" in label:
            qid = travel_gene_dict(marker, "mouse")

            data_for_item.append(
                wdi_core.WDItemID(value=qid, prop_nr="P8872", references=references)
            )
            print(qid)
            cell_type_id = subclass_dict[row["cell class"]]
            print(cell_type_id)
            wd_item = wdi_core.WDItemEngine(
                wd_item_id=cell_type_id,
                data=data_for_item,
                append_value=["P8872"],
            )
            print(wd_item)
            wd_item.write(login_instance)
        break
