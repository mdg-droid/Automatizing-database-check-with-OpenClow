from notion_client import Client

from config import NOTION_TOKEN, SUBCOMPETENZE_DATA_SOURCE_ID

notion = Client(auth=NOTION_TOKEN)

FIELDS_TO_CHECK = [
    "Status",
    "Tipologia",
    "Paese HQ",
    "Data di fondazione",
    "Dominio principale",
    "Subcompetenze",
    "Fatturato stimato recente",
    "Finanziamenti pubblici",
    "Investitori principali",
    "Brevetti & IP",
    "Altri paesi",
]

FIELD_SPECS = {
    "Status": {
        "description": "État actuel de l'entreprise.",
        "valeurs_possibles": ["Active", "Acquired", "Merged", "Inactive", "Bankrupt", "Unknown", "Partly acquired"],
    },
    "Tipologia": {
        "description": "Type d'organisation.",
        "valeurs_possibles": ["Startup", "PMI", "Large Corporate", "Agenzia Spaziale",
                               "Centro di Ricerca / Università", "Incubatore / Acceleratore",
                               "Fondo VC / BA", "Scale-up", "Altro"],
    },
    "Paese HQ": {
        "description": "Pays du siège social (HQ), pas des filiales.",
        "valeurs_possibles": ["Italia", "Germania", "Austria", "Svizzera", "Francia", "UK", "Spagna",
                               "Paesi Bassi", "Lussemburgo", "Svezia", "Finlandia", "Norvegia",
                               "Danimarca", "Belgio", "Extra-EU", "Altro"],
    },
    "Data di fondazione": {
        "description": "Année (ou date) de fondation officielle de l'entreprise.",
        "valeurs_possibles": None,
    },
    "Dominio principale": {
        "description": "Un ou plusieurs domaines d'activité principaux.",
        "valeurs_possibles": ["Spazio", "Aeronautica", "Difesa & Sicurezza"],
    },
    "Subcompetenze": {
        "description": "Sous-compétences techniques précises de l'entreprise (ex: propulsion électrique, "
                        "segment sol, observation de la Terre...).",
        "valeurs_possibles": None,
    },
    "Fatturato stimato recente": {
        "description": "Chiffre d'affaires estimé le plus récent connu pour l'entreprise. Souvent une "
                        "estimation approximative pour les entreprises non cotées : ne juge \"faux\" que "
                        "si l'écart avec des sources fiables est net (ex: facteur 2 ou plus), pas pour une "
                        "estimation proche.",
        "valeurs_possibles": None,
    },
    "Finanziamenti pubblici": {
        "description": "Financements publics reçus (subventions, contrats institutionnels, programmes "
                        "ESA/UE/nationaux...).",
        "valeurs_possibles": None,
    },
    "Investitori principali": {
        "description": "Principaux investisseurs privés (VC, business angels, corporate venture...).",
        "valeurs_possibles": None,
    },
    "Brevetti & IP": {
        "description": "Brevets déposés ou propriété intellectuelle notable détenue par l'entreprise.",
        "valeurs_possibles": None,
    },
    "Altri paesi": {
        "description": "Autres pays où l'entreprise a une présence significative (filiale, bureau, usine), "
                        "en plus du pays du HQ.",
        "valeurs_possibles": None,
    },
}


def extract_value(prop: dict):
    """
    Extrait une valeur lisible d'une propriété Notion brute (format renvoyé par notion_client),
    quel que soit son type (select, status, multi_select, rich_text, title, relation, number...).
    """
    if prop is None:
        return None

    prop_type = prop.get("type")

    if prop_type == "title":
        return "".join(t["plain_text"] for t in prop["title"]) or None

    if prop_type == "rich_text":
        return "".join(t["plain_text"] for t in prop["rich_text"]) or None

    if prop_type == "select":
        return prop["select"]["name"] if prop["select"] else None

    if prop_type == "status":
        return prop["status"]["name"] if prop["status"] else None

    if prop_type == "multi_select":
        return [o["name"] for o in prop["multi_select"]]

    if prop_type == "number":
        return prop["number"]

    if prop_type == "checkbox":
        return prop["checkbox"]

    if prop_type == "url":
        return prop["url"]

    if prop_type == "relation":
        # Résolu séparément via get_display_value() / resolve_relation_titles() :
        # cette branche ne devrait normalement plus être atteinte pour "Subcompetenze".
        ids = [r["id"] for r in prop["relation"]]
        return f"{len(ids)} élément(s) lié(s) (relation, ids: {ids})"

    if prop_type == "date":
        return prop["date"]["start"] if prop["date"] else None

    # Fallback générique si un type non prévu apparaît.
    return prop.get(prop_type)


def is_empty(value) -> bool:
    """
    Détermine si une valeur doit être considérée comme "non renseignée" et donc
    exclue du prompt. 0 est volontairement traité comme une valeur valide
    (ex: un financement public à 0 est une info, pas une absence d'info).
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


_subcompetenze_cache: dict[str, str] | None = None


def _load_subcompetenze_map() -> dict[str, str]:
    """
    Charge une seule fois id -> nom pour toutes les sous-compétences,
    via une requête paginée sur la data source dédiée (pas une requête par player).
    """
    mapping = {}
    cursor = None

    while True:
        kwargs = {"data_source_id": SUBCOMPETENZE_DATA_SOURCE_ID, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor

        response = notion.data_sources.query(**kwargs)

        for page in response["results"]:
            title_prop = next(
                (p for p in page["properties"].values() if p["type"] == "title"),
                None
            )
            if title_prop and title_prop["title"]:
                mapping[page["id"]] = title_prop["title"][0]["plain_text"]

        if not response["has_more"]:
            break
        cursor = response["next_cursor"]

    return mapping


def get_subcompetenze_map() -> dict[str, str]:
    global _subcompetenze_cache
    if _subcompetenze_cache is None:
        _subcompetenze_cache = _load_subcompetenze_map()
    return _subcompetenze_cache


def resolve_relation_titles(prop: dict) -> list[str]:
    """
    Résout les IDs d'un champ relation Notion en titres lisibles, via le cache
    en mémoire construit au premier appel (voir get_subcompetenze_map).
    """
    if prop is None or prop.get("type") != "relation":
        return []

    id_to_name = get_subcompetenze_map()
    return [id_to_name.get(ref["id"], f"(inconnu: {ref['id']})") for ref in prop["relation"]]



def get_display_value(field: str, prop: dict):
    """
    Comme extract_value(), mais résout les relations en noms lisibles
    pour les champs qui en ont besoin (ex: Subcompetenze).
    """
    if prop is not None and prop.get("type") == "relation":
        return resolve_relation_titles(prop)
    return extract_value(prop)


def build_prompt(player: dict) -> str:
    """
    Construit le prompt envoyé à OpenClaw pour vérifier un player via son navigateur interne.
    Les champs vides ou non renseignés dans Notion sont exclus du prompt : on ne demande
    jamais à OpenClaw de vérifier une information qu'on n'a pas.
    """
    properties = player["properties"]
    name = extract_value(properties["Nome del player"]) or "Nom inconnu"

    lines = [
        f"Tu dois vérifier des informations d'entreprise pour '{name}', dans le secteur "
        f"spatial/aéronautique/défense, en effectuant une recherche web RÉELLE et APPROFONDIE.",
        "",
        "MÉTHODE OBLIGATOIRE (ne réponds pas sans l'avoir suivie) :",
        "1. Cherche et consulte le site officiel de l'entreprise.",
        "2. Cherche et consulte sa page LinkedIn officielle.",
        "3. Si les deux sources précédentes ne suffisent pas ou se contredisent, cherche une "
        "troisième source fiable (registre d'entreprise, article de presse spécialisé, Crunchbase...).",
        "4. Ne conclus JAMAIS à partir d'une seule page ou de ta mémoire seule : si tu n'as pas "
        "pu consulter au moins deux sources indépendantes pour un champ, marque-le comme "
        "\"non vérifiable\" plutôt que vrai ou faux.",
        "",
        "Seuls les champs listés ci-dessous doivent être vérifiés (les champs vides dans notre "
        "base ont été omis intentionnellement, ne les invente pas et ne les commente pas) :",
        "",
    ]

    checked_any = False

    for field in FIELDS_TO_CHECK:
        prop = properties.get(field)
        value = get_display_value(field, prop)

        if is_empty(value):
            continue

        checked_any = True
        spec = FIELD_SPECS[field]
        lines.append(f"- {field}")
        lines.append(f"  Définition : {spec['description']}")
        if spec["valeurs_possibles"]:
            lines.append(f"  Valeurs possibles : {', '.join(spec['valeurs_possibles'])}")
        lines.append(f"  Valeur enregistrée : {value}")

    if not checked_any:
        lines.append("(Aucun champ renseigné à vérifier pour ce player.)")

    lines += [
        "",
        "RÈGLES DE JUGEMENT :",
        "- Un champ est \"faux\" seulement si tu as une preuve concrète et sourcée qui contredit "
        "la valeur enregistrée.",
        "- Un champ que tu n'as pas réussi à confirmer doit aller dans \"unverifiable_fields\", "
        "PAS dans \"false_fields\".",
        "- Une différence mineure de formulation qui désigne la même réalité n'est pas une erreur "
        "(ex: \"Torino\" vs \"Turin\").",
        "",
        "Réponds UNIQUEMENT avec un JSON strict, sans aucun texte autour, de cette forme exacte :",
        '{'
        '"data_check": "True data" | "False data", '
        '"false_fields": ["<nom du champ>", ...], '
        '"unverifiable_fields": ["<nom du champ>", ...], '
        '"sources": ["<url>", ...], '
        '"notes": "<1-2 phrases expliquant les points litigieux, ou vide si tout est confirmé>"'
        '}',
    ]

    return "\n".join(lines)
