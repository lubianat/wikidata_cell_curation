
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

    }
}

instance_dict = {
    "cell type":"Q189118",
    "cell class":"Q104852483",
    "cell state":"Q104539563"
}

part_of_dict = {
    "ventral cochlear nucleus (VCN)":"Q4771335",
    "placental villi":"Q2272222",
    "fetal liver":"Q104539102",
    "epididymis": "Q1973610",
    "prostate": "Q9625",
    "spleen": "Q9371",
    "epidermis": "Q796482",
    "thymus": "Q163987",
    "thymic medulla": "Q107446186",
    "interfollicular epidermis": "Q106385904",
    "hair follicle": "Q866324",
    "peritoneal cavity": "Q1030169",
    "liver":"Q9368",
    "airways": "Q13400765",
    "bronchius": "Q181602",
    "esophagus": "Q173710",
    "retina": "Q169342",
    "brain": "Q1073",
    "lung": "Q7886",
    "sciatic nerve": "Q307869",
    "cochlea" : "Q317857",
    "spiral ganglion": "Q3095145",
    "dorsal root ganglion": "Q1395415",
    "colon": "Q5982337",
    "kidney": "Q9377",
    "dura mater": "Q1394389",
    "pancreas": "Q9618",
    "placenta": "Q1212935",
    "intestine": "Q9639"

}