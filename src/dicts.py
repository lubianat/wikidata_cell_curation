import json
import os, json

dicts = {}

path_to_json = "dictionaries"
json_files = [
    pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith(".json")
]

for json_file in json_files:
    keyword = json_file.split(".")[0]
    with open(f"dictionaries/{keyword}.json") as f:
        dicts[keyword] = json.loads(f.read())


# List is needed so parsing is ordered. 
# Names might be nested (e.g. "naked mole rat" and "rat")
species_list = ["mouse", "human", "zebrafish", "sheep", "marmoset", "hamster", "macaque", "rat", "Middle East blind mole rat"]
species_list.sort(key = len)
species_list.reverse()

species_dict = {

    "mouse" :{
        "qid": "Q83310",
        "species_name": "Mus musculus"
    }, 

    "human": {
        "qid":"Q15978631",
        "species_name": "Homo sapiens"
    }, 

    "zebrafish": {
        "qid":"Q15978631",
        "species_name": "Danio rerio"
    },

    "sheep": {
        "qid": "Q29350771",
        "species_name": "Ovis aries"
    },

    "marmoset": {
        "qid":"Q838947",
        "species_name": "Callithrix jacchus"
    },

    "macaque": {
        "qid": "Q301676",
        "species_name": "Macaca fascicularis"
    },


    "rhesus": {
        "qid": "Q156606",
        "species_name": "Macaca mulatta"
    },
    "hamster": {
        "qid": "Q204175",
        "species_name": "Mesocricetus auratus"
    },

    "rat": {
        "qid": "Q184224",
        "species_name": "Rattus norvegicus"
    },

    "Middle East blind mole rat": {
        "qid": "Q13422405",
        "species_name": "Spalax ehrenbergi"
    },

    "Nematostella vectensis" : {
        "qid": "Q139440",
        "species_name": "Nematostella vectensis"

    }, 
    "primate " : {
        "qid": "Q7380",
        "species_name": "primates"

    }, 

}

instance_dict = {
    "cell type":"Q189118",
    "cell class":"Q104852483",
    "cell state":"Q104539563",
    "lipotype": "Q111649907",
    "Q111649907": "Q111649907"
}
