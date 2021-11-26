import requests
import json


def prepare_dictionary(sparql_query, entity_type, base_dir="dictionaries/"):
    """

    Saves a dictionary with aliases and Wikidata IDs for each of the entities retrieved by the query.

    Arguments:
        sparql_query: A Wikidata SPARQL query to retrieve the labels and the ids of interest
        entity_type: The entity type for the dictionary. This will be used to label the dictionary 
    """

    endpoint_url = "https://query.wikidata.org/sparql"

    response = requests.get(
        endpoint_url,
        params={"query": sparql_query, "format": "json"},
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        },
    )
    print(response)
    query_result = response.json()
    data = query_result["results"]["bindings"]

    entity_dict = {}
    for row in data:
        qid = row["item"]["value"].replace("http://www.wikidata.org/entity/", "")
        label = row["label"]["value"]
        entity_dict[label] = qid

    entity_dict = json.dumps(entity_dict, indent=4)
    with open(f"{base_dir}{entity_type}.json", "w") as f:
        f.write(entity_dict)


print("Preparing the human genes dictionary")
# Considering a gene as anything that has a P353 (HGNC gene symbol).
human_genes_query = """
# human_genes on Wikidata
SELECT DISTINCT ?label ?item
WHERE 
{
  {?item wdt:P353 ?any .}

  { ?item skos:altLabel ?label . }
  UNION
  { ?item rdfs:label ?label . }
  
  FILTER(LANG(?label) = "en")
}
"""

prepare_dictionary(sparql_query=human_genes_query, entity_type="human_gene")

mouse_genes_query = """
# mouse_genes on Wikidata
SELECT DISTINCT ?label ?item
WHERE 
{
  {
    ?item wdt:P31 wd:Q7187 .
    ?item wdt:P703 wd:Q83310 . 
  }

  { ?item skos:altLabel ?label . }
  UNION
  { ?item rdfs:label ?label . }
  
  FILTER(LANG(?label) = "en")
}
"""
prepare_dictionary(sparql_query=mouse_genes_query, entity_type="mouse_gene")


zebrafish_genes_query = """
# zebrafish_genes on Wikidata
SELECT DISTINCT ?label ?item
WHERE 
{
  {
    ?item wdt:P31 wd:Q7187 .
    ?item wdt:P703 wd:Q169444 . 
  }

  { ?item skos:altLabel ?label . }
  UNION
  { ?item rdfs:label ?label . }
  
  FILTER(LANG(?label) = "en")
}
"""
prepare_dictionary(sparql_query=zebrafish_genes_query, entity_type="zebrafish_gene")
