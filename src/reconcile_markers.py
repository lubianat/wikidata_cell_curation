import json
import os
from pathlib import Path
import pandas as pd
import logging
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config as wbi_config
from login import USER, PASS
from wdcuration import WikidataDictAndKey

# Setup logging
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Login to Wikibase
login_instance = wbi_login.Clientlogin(user=USER, password=PASS)
wbi = WikibaseIntegrator(login=login_instance)
wbi_config["USER_AGENT"] = "Marker Reconciler (by TiagoLubiana)"

# Set up paths
HERE = Path(__file__).parent.resolve()
DATA = HERE.parent.joinpath("data").resolve()
DICTS = HERE.parent.joinpath("dictionaries").resolve()

# Force refresh Google Sheets data
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub?gid=844768758&single=true&output=csv"
cell_markers = pd.read_csv(
    sheet_url + "&cachebust=" + str(pd.Timestamp.now().timestamp())
)


def split_markers(marker_string):
    """Split marker strings into a list of individual markers."""
    replacements = ["+", "(", ")", "/", "  ", ";", " or "]
    for r in replacements:
        marker_string = marker_string.replace("and", ",")
        marker_string = marker_string.replace(r, ",")
    return [s.strip() for s in marker_string.split(",")]


# Load cell type dictionaries
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
    """Retrieve gene QID from the dictionary based on gene name and species."""
    path = DICTS.joinpath(f"{species}_gene.json")
    gene_dict = json.loads(path.read_text())
    return gene_dict.get(gene_name)


# Load existing missing items to avoid duplicates
missing_items_path = DATA.joinpath("missing_items.txt")
if missing_items_path.exists():
    with open(missing_items_path, "r") as file:
        existing_missing_items = set(file.read().splitlines())
else:
    existing_missing_items = set()

# Process each cell marker
for index, row in cell_markers.iterrows():
    marker_labels = row["marker "].strip()
    marker_list = split_markers(marker_labels)

    # Prepare references
    source_qid = row["stated in"].strip()
    if pd.isna(row["stated as"]):
        references = [[datatypes.Item(value=source_qid, prop_nr="P248")]]
    else:
        clean_string = (
            row["stated as"]
            .strip()
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\t", " ")
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
    logging.warning(f"Processing cell class: {label}")

    try:
        cell_dict = cell_dict_object.master_dict["celltypes_dict"]
        cell_qid = cell_dict[label]
        entity = wbi.item.get(cell_qid)
    except KeyError:
        logging.warning(f"Item for {label} not found. Attempting to create.")
        cell_dict_object.string = label
        cell_dict_object.dict_key = label
        cell_dict_object.add_key()
        cell_dict_object.save_dict()
        try:
            cell_dict = cell_dict_object.master_dict["celltypes_dict"]
            entity = wbi.item.get(cell_dict[label])
        except KeyError:
            logging.error(f"Failed to create item for {label}")
            if label not in existing_missing_items:
                existing_missing_items.add(label)
                with open(missing_items_path, "a") as file:
                    file.write(label + "\n")
        continue

    # Get initial state of claims
    initial_claims = set(entity.claims.get_json())

    changes_made = False
    for marker in marker_list:
        logging.warning(f"Processing marker: {marker}")
        gene_qid = travel_gene_dict(marker, "human" if "human" in label else "mouse")
        if not gene_qid:
            if marker:
                logging.warning(f"Gene not found: {marker}")
                action = input(
                    "Press 'a' to enter QID manually or any other key to continue: "
                )
                if action.lower() == "a":
                    gene_qid = input(f"Enter QID for gene {marker}: ").strip()
                    if gene_qid:
                        # Optionally, you can validate the entered QID format here
                        new_claim = datatypes.Item(
                            prop_nr="P8872", value=gene_qid, references=references
                        )
                        entity.claims.add(
                            new_claim,
                            action_if_exists=ActionIfExists.MERGE_REFS_OR_APPEND,
                        )
                        changes_made = True
                    continue
            if marker not in existing_missing_items:
                existing_missing_items.add(marker)
                with open(missing_items_path, "a") as file:
                    file.write(marker + "\n")
            continue

        new_claim = datatypes.Item(
            prop_nr="P8872", value=gene_qid, references=references
        )
        entity.claims.add(
            new_claim, action_if_exists=ActionIfExists.MERGE_REFS_OR_APPEND
        )
        changes_made = True

    # Get final state of claims
    final_claims = set(entity.claims.get_json())

    if changes_made:
        entity.write(summary=f"Add curated marker(s) for {label}.")
        logging.warning(
            f"Changes written to Wikidata for {label}. Link: https://www.wikidata.org/wiki/{cell_qid}"
        )
        input(
            "Press Enter to continue..."
        )  # Pause when markers are added to a cell type with actual changes

# Save missing items
with open(missing_items_path, "w") as file:
    for item in existing_missing_items:
        file.write(item + "\n")
