import json
import os
from pathlib import Path
import pandas as pd
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config as wbi_config
from login import USER, PASS
from wdcuration import WikidataDictAndKey

login_instance = wbi_login.Clientlogin(user=USER, password=PASS)
wbi = WikibaseIntegrator(login=login_instance)
wbi_config["USER_AGENT"] = "Marker Reconciler (by TiagoLubiana)"

HERE = Path(__file__).parent.resolve()
DATA = HERE.parent.joinpath("data").resolve()
DICTS = HERE.parent.joinpath("dictionaries").resolve()


cell_markers = pd.read_csv(
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub?gid=844768758&single=true&output=csv"
)


def split_markers(marker_string):
    replacements = ["+", "(", ")", "/", "  "]
    for r in replacements:
        marker_string = marker_string.replace("and", ",")
        marker_string = marker_string.replace(r, ",")
    return [s.strip() for s in marker_string.split(",")]


cell_type_dict = json.loads(DICTS.joinpath("celltypes_dict.json").read_text())
cell_type_dict.update(
    json.loads(DICTS.joinpath("cell_types_from_wiki.json").read_text())
)

cell_dict_object = WikidataDictAndKey(
    master_dict={"celltypes_dict": cell_type_dict},
    dict_name="celltypes_dict",
    path=DICTS,
    new_item_config=None,
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
    marker_list = split_markers(marker_labels)

    # References if there is a stated as value:
    # Test if row value is nan:

    source_qid = row["stated in"].strip()
    if pd.isna(row["stated as"]):
        references = [[datatypes.Item(value=source_qid, prop_nr="P248")]]
    else:
        trimmed_string = row["stated as"].strip()
        clean_string = (
            trimmed_string.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        )

        references = [
            [
                datatypes.MonolingualText(
                    text=clean_string, prop_nr="P1683", language="en"
                ),
                datatypes.Item(value=source_qid, prop_nr="P248"),
            ]
        ]

    label = row["cell class"]
    print(f"Running code for {label} ")
    try:
        cell_dict = cell_dict_object.master_dict["celltypes_dict"]
        cell_qid = cell_dict[label]
        entity = wbi.item.get(cell_qid)
    except KeyError:
        print(f"Item for {label} not found")
        cell_dict_object.string = label
        cell_dict_object.dict_key = label
        cell_dict_object.add_key()
        cell_dict_object.save_dict()
        try:
            cell_dict = cell_dict_object.master_dict["celltypes_dict"]
            entity = wbi.item.get(cell_dict[label])
        except:
            if label not in existing_missing_items:
                existing_missing_items.add(label)
                with open(missing_items_path, "a") as file:
                    file.write(label + "\n")
        continue

    for marker in marker_list:
        print(marker)
        gene_qid = travel_gene_dict(marker, "human" if "human" in label else "mouse")
        if not gene_qid:
            print(f"======== GENE NOT FOUND -- {marker}=========")
            if marker not in existing_missing_items:
                existing_missing_items.add(marker)
                with open(missing_items_path, "a") as file:
                    file.write(marker + "\n")
            break

        if gene_qid:
            new_claim = datatypes.Item(
                prop_nr="P8872", value=gene_qid, references=references
            )
            entity.claims.add(
                new_claim, action_if_exists=ActionIfExists.MERGE_REFS_OR_APPEND
            )
            entity.write(summary=f"Add curated marker ({marker}).")
