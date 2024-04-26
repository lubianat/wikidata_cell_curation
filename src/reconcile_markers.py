import json
import os
from pathlib import Path
import pandas as pd
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config as wbi_config
from login import USER, PASS

login_instance = wbi_login.Clientlogin(user=USER, password=PASS)
wbi = WikibaseIntegrator(login=login_instance)
wbi_config["USER_AGENT"] = "Marker Reconciler (by TiagoLubiana)"

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
    replacements = ["+", "(", ")"]
    for r in replacements:
        marker_string = marker_string.replace(r, " ")
    return [s.replace("and", "").strip() for s in marker_string.split(",")]


cell_type_dict = json.loads(DICTS.joinpath("celltypes_dict.json").read_text())
cell_type_dict.update(
    json.loads(DICTS.joinpath("cell_types_from_wiki.json").read_text())
)


def travel_gene_dict(gene_name, species):
    path = DICTS.joinpath(f"{species}_gene.json")
    gene_dict = json.loads(path.read_text())
    return gene_dict.get(gene_name)


# Load existing missing items to a set to avoid duplicates
missing_items_path = DATA.joinpath("missing_items.txt")
if missing_items_path.exists():
    with open(missing_items_path, "r") as file:
        existing_missing_items = set(file.read().splitlines())
else:
    existing_missing_items = set()

for index, row in cell_markers.iterrows():
    marker_labels = row["marker "].strip()
    print(marker_labels)

    marker_list = split_markers(marker_labels)

    references = [
        [
            datatypes.MonolingualText(
                text=row["stated as"], prop_nr="P1683", language="en"
            ),
            datatypes.Item(value=row["stated in"], prop_nr="P248"),
        ]
    ]

    label = row["cell class"]
    print(f"Running code for {label} ")
    try:
        entity = wbi.item.get(cell_type_dict[label])
    except KeyError:
        print(f"Item for {label} not found")
        if label not in existing_missing_items:
            existing_missing_items.add(label)
            with open(missing_items_path, "a") as file:
                file.write(label + "\n")
        continue

    for marker in marker_list:
        print(marker)
        gene_qid = travel_gene_dict(marker, "human" if "human" in label else "mouse")
        print(gene_qid)

        if not gene_qid:
            if label not in existing_missing_items:
                existing_missing_items.add(label)
                with open(missing_items_path, "a") as file:
                    file.write(label + "\n")
            break

        new_claim = datatypes.Item(
            prop_nr="P8872", value=gene_qid, references=references
        )
        entity.claims.add(
            new_claim, action_if_exists=ActionIfExists.MERGE_REFS_OR_APPEND
        )
        entity.write(summary="Add marker for cell type curated from the literature.")
