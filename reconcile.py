#!/usr/bin/env python3

import json
import os
import re
import time
import traceback
import pandas as pd

from wdcuration import add_key
from wikidataintegrator import wdi_core, wdi_login

from src.dicts import DICTS, SPECIES_DICT, INSTANCE_DICT
from src.login import *


def main():
    # Download data from Google Sheet
    os.system(
        "wget -O data/cell_classes.xlsx https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub\?output\=xlsx"
    )

    # Load data from the downloaded file
    cells_df = pd.read_excel("data/cell_classes.xlsx", sheet_name="cell classes")

    print("###### Biocuration of Cell Classes Table ######")
    print(cells_df.head())

    # Initialize login
    login_instance = wdi_login.WDLogin(user="TiagoLubiana", pwd=WDPASS)

    # Iterate over each row of the table and create corresponding Wikidata items
    for _, row in cells_df.iterrows():
        label = row["label"]
        print(f"Running code for {label} ")

        # Skip rows with labels that have already been processed
        if label in DICTS["celltypes_dict"]:
            continue

        # Create references for the statements
        stated_in_full_reference = wdi_core.WDItemID(
            value=row["stated in"], prop_nr="P248", is_reference=True
        )
        references = [[stated_in_full_reference]]

        # Determine the species of the cell type and set description accordingly
        species = get_species_from_label(label)
        if species:
            species_qid = species["qid"]
            species_name = species["species_name"]
            description = f"cell type in {species_name}"
            data_for_item = [
                wdi_core.WDItemID(
                    value=species_qid, prop_nr="P703", references=references
                )
            ]
        else:
            description = "cell type"
            data_for_item = []

        try:
            # Add subclass of (P279) statements
            subclass_of_statement = get_integrator_statement(
                row, "P279", "celltypes_dict", "subclass of"
            )
            data_for_item.append(subclass_of_statement)

            # Add term in higher taxon (P10019) statements
            higher_taxon_statement = get_higher_taxon_statement(row)
            if higher_taxon_statement:
                data_for_item.append(higher_taxon_statement)

            # Add develops from (P3094) statements
            develops_from_statement = get_integrator_statement(
                row, "P3094", "celltypes_dict", "develops from"
            )
            if develops_from_statement:
                data_for_item.append(develops_from_statement)

            # Add anatomical location (P927) statements
            location_statement = get_integrator_statement(
                row, "P927", "part_of", "anatomical location"
            )
            if location_statement:
                data_for_item.append(location_statement)

            # Add article that describes item via "described by source" (P1343) statement
            if str(row["described by source"]) != "nan":
                data_for_item.append(
                    wdi_core.WDItemID(value=row["described by source"], prop_nr="P1343")
                )

            # Add instances of "cell type"
            instance = INSTANCE_DICT.get(row["instance of"], INSTANCE_DICT["cell type"])
            data_for_item.append(
                wdi_core.WDItemID(value=instance, prop_nr="P31", references=references)
            )

            # Create a new Wikidata item and add aliases, labels and descriptions
            wd_item = wdi_core.WDItemEngine(data=data_for_item)
            aliases = row["aliases"].split("|") if str(row["aliases"]) != "nan" else []
            wd_item.set_label(label=label, lang="en")
            wd_item.set_aliases(aliases, lang="en")
            wd_item.set_description(description, lang="en")

            # Write the new Wikidata item to the Wikidata database and add the label to the celltypes_dict
            try:
                wd_item.write(login_instance)
                DICTS["celltypes_dict"][label] = wd_item.wd_item_id
            except Exception as e:
                print(f"Error: {e}")

        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")
            break

        time.sleep(1)

    # Write updated celltypes_dict to file
    write_dict(DICTS["celltypes_dict"], "celltypes_dict")


def get_species_from_label(label):
    """
    Determine the species of the cell type from its label.
    """
    for species in SPECIES_DICT:
        if species in label:
            return SPECIES_DICT[species]
    return None


def get_higher_taxon_statement(row):
    """
    Return a Wikidata statement for the "term in higher taxon" field of a row.
    """
    higher_taxon_term = str(row["term in higher taxon"]).strip()
    if higher_taxon_term == "nan":
        return None
    if re.findall("Q[0-9]*", higher_taxon_term):
        higher_taxon_qid = higher_taxon_term
    else:
        higher_taxon_dict = add_key(DICTS["celltypes_dict"], higher_taxon_term)
        write_dict(higher_taxon_dict, "celltypes_dict")
        higher_taxon_qid = higher_taxon_dict[higher_taxon_term]
    return wdi_core.WDItemID(value=higher_taxon_qid, prop_nr="P10019")


def get_integrator_statement(row, prop_nr, reference_dict_name, rowname):
    """
    Return a Wikidata statement for a specific property of a row.
    """
    term = str(row[rowname]).strip()
    if term == "nan":
        return None
    if re.findall("Q[0-9]*", term):
        subclass = term
    else:
        reference_dict = DICTS[reference_dict_name]
        if term not in reference_dict:
            reference_dict = add_key(reference_dict, term)
        write_dict(reference_dict, reference_dict_name)
        subclass = reference_dict[term]
    return wdi_core.WDItemID(value=subclass, prop_nr=prop_nr)


def write_dict(reference_dict, reference_dict_name):
    """
    Write a dictionary to a file.
    """
    with open(f"dictionaries/{reference_dict_name}.json", "w+") as f:
        f.write(json.dumps(reference_dict, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()
