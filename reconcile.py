#!/usr/bin/env python3

import json
import os
from pathlib import Path
import pandas as pd
import logging

from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config as wbi_config

from src.login import USER, PASS
from wdcuration import WikidataDictAndKey, add_key

from src.dicts import DICTS, SPECIES_DICT, INSTANCE_DICT
import re
import time

# Setup logging
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)

NAME_TO_PID = {
    "stated in": "P248",
    "subclass of": "P279"
}

NAME_TO_QID_DICT = {
    "subclass of": "celltypes_dict"
}

def get_quick_item_prop(
                        source,
                        header, 
                        data_for_item = [],
                        qid_dict_dict = NAME_TO_QID_DICT,
                        pid_dict=NAME_TO_PID,
                        with_reference=True,
                        append_to_data = True):
    if with_reference:
        references = [[get_quick_item_prop(source, "stated in", with_reference=False)]]
        
        try:
         targets = source[header].split(sep="|")
        except AttributeError: 
            print(f"No value found for '{header}' while processing {source['label']}")
            quit()
        if len(targets)> 1:
            for target in targets:
                target = target.strip() 
                data_for_item.append(get_quick_item_prop(source = {header:target, "stated in":source["stated in"]},
                    header = header,
                    data_for_item = data_for_item,
                    append_to_data=False))
        else:
            target = targets[0]

        if re.findall("Q[0-9]*", target):
            target_qid = target

        else:
            reference_dict = DICTS[qid_dict_dict[header]]
            if target not in reference_dict:
                reference_dict = add_key(reference_dict, target)
                write_dict(reference_dict, qid_dict_dict[header])
            target_qid = reference_dict[target]
        
        statement = datatypes.Item(value=target_qid, prop_nr=pid_dict[header],
                              references=references)
        if append_to_data ==False:
            return statement
        else:
            data_for_item.append(statement)
            return(data_for_item)
        
    else:
        return datatypes.Item(value=source[header], prop_nr=pid_dict[header])



def main():

    cells_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vTanLtzxD6OXpu3Ze4aNITlIMZEqfK3qrrcNiwFE6kA-YVnuzULp3dG3oYIe5gYAVj28QWZnGwzN_H6/pub?gid=0&single=true&output=csv")

    print("###### Biocuration of Cell Classes Table ######")
    print(cells_df.head())

    login_instance = wbi_login.Clientlogin(user=USER, password=PASS)
    wbi = WikibaseIntegrator(login=login_instance)
    wbi_config["USER_AGENT"] = "Cell Reconciler (by TiagoLubiana)"

    for _, row in cells_df.iterrows():

        label = row["label"]
        if label in DICTS["celltypes_dict"]:
            continue

        print(f"Running code for {label} ")

        references = [[get_quick_item_prop(row, "stated in", with_reference=False)]]
        
        # Determine the species of the cell type and set description accordingly
        species = get_species_from_label(label)
        if species:
            species_qid = species["qid"]
            species_name = species["species_name"]
            description = f"cell type in {species_name}"
            data_for_item = [
                datatypes.Item(
                    value=species_qid, prop_nr="P703", references=references
                )
            ]
        else:
            description = "cell type"
            data_for_item = []

        # Add subclass of (P279) statements
        data_for_item = get_quick_item_prop(row, "subclass of", data_for_item)

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
                datatypes.Item(value=row["described by source"], prop_nr="P1343")
            )

        # Add instances of "cell type"
        instance = INSTANCE_DICT.get(row["instance of"], INSTANCE_DICT["cell type"])
        data_for_item.append(
            datatypes.Item(value=instance, prop_nr="P31", references=references)
        )

        # Create a new Wikidata item and add aliases, labels and descriptions
        entity = wbi.item.new()
        for claim in data_for_item:
            entity.claims.add(claim)

        aliases = row["aliases"].split("|") if str(row["aliases"]) != "nan" else []
        entity.labels.set("en",label)
        for alias in aliases:
            print(alias)
            entity.aliases.set("en", alias)
        entity.descriptions.set("en", description)

        # Write the new Wikidata item to the Wikidata database and add the label to the celltypes_dict
        try:
            entity.write()
            DICTS["celltypes_dict"][label] = entity.id
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(2)

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
    return datatypes.Item(value=higher_taxon_qid, prop_nr="P10019")


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
    return datatypes.Item(value=subclass, prop_nr=prop_nr)


def write_dict(reference_dict, reference_dict_name):
    """
    Write a dictionary to a file.
    """
    with open(f"dictionaries/{reference_dict_name}.json", "w+") as f:
        f.write(json.dumps(reference_dict, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()
