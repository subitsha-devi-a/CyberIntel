
import json
import re
from pathlib import Path

import networkx as nx


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "threats.json"
)


# Known aliases for entities in the current CyberIntel dataset.
ENTITY_ALIASES = {
    "TH001": [
        "Log4Shell",
        "CVE-2021-44228",
        "Log4Shell vulnerability"
    ],
    "TH002": [
        "Apache Log4j",
        "Log4j",
        "Java logging framework"
    ],
    "TH003": [
        "Remote Code Execution",
        "RCE",
        "arbitrary code execution"
    ],
    "TH004": [
        "MITRE ATT&CK T1190",
        "T1190",
        "Exploit Public-Facing Application"
    ]
}


def load_threats():
    """Load cybersecurity records from the JSON dataset."""

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text):
    """Convert text into a searchable lowercase string."""

    return str(text or "").lower()


def find_entity_mentions(text, graph):
    """Identify known cybersecurity entities in document text."""

    text = normalize_text(text)
    matched_entities = []

    for node, details in graph.nodes(data=True):
        aliases = ENTITY_ALIASES.get(node, [])

        # Include the entity's actual title as an alias.
        aliases = aliases + [details.get("label", "")]

        for alias in aliases:
            alias = normalize_text(alias).strip()

            if not alias:
                continue

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, text):
                matched_entities.append(node)
                break

    return matched_entities


def extract_evidence(text, first_entity, second_entity):
    """Return a sentence containing both entities as evidence."""

    sentences = re.split(r"(?<=[.!?])\s+", str(text or ""))

    aliases_first = ENTITY_ALIASES.get(first_entity, [])
    aliases_second = ENTITY_ALIASES.get(second_entity, [])

    for sentence in sentences:
        mentions = find_entity_mentions_in_sentence(
            sentence,
            aliases_first,
            aliases_second
        )

        if mentions:
            return sentence.strip()[:500]

    return ""


def find_entity_mentions_in_sentence(sentence, aliases_first, aliases_second):
    """Check whether a sentence contains aliases for both entities."""

    sentence = normalize_text(sentence)

    def contains_alias(aliases):
        for alias in aliases:
            alias = normalize_text(alias).strip()

            if not alias:
                continue

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(alias)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, sentence):
                return True

        return False

    return (
        contains_alias(aliases_first)
        and contains_alias(aliases_second)
    )


def infer_relationship(first_id, second_id, evidence):
    """Infer a relationship using transparent text-pattern rules."""

    text = normalize_text(evidence)

    first_category = first_id
    second_category = second_id

    # Vulnerability -> affected software
    if (
        first_category == "TH001"
        and second_category == "TH002"
    ) or (
        first_category == "TH002"
        and second_category == "TH001"
    ):
        if re.search(
            r"\b(affects|impacts|vulnerability in|"
            r"vulnerable in|flaw in|issue in)\b",
            text
        ):
            return "AFFECTS"

    # Vulnerability -> attack impact
    if (
        first_category == "TH001"
        and second_category == "TH003"
    ) or (
        first_category == "TH003"
        and second_category == "TH001"
    ):
        if re.search(
            r"\b(can lead to|leads to|results in|"
            r"allows|enables|remote code execution|"
            r"arbitrary code execution)\b",
            text
        ):
            return "CAN_ENABLE"

    # Vulnerability -> MITRE technique
    if (
        first_category == "TH001"
        and second_category == "TH004"
    ) or (
        first_category == "TH004"
        and second_category == "TH001"
    ):
        if re.search(
            r"\b(mapped to|mapping|associated with|"
            r"technique|exploitation|exploit)\b",
            text
        ):
            return "POTENTIAL_TECHNIQUE_MAPPING"

    return None


def add_relationship(graph, source, target, relation, evidence, method):
    """Add a relationship without overwriting an existing one."""

    if source == target:
        return

    # Preserve manually seeded relationships.
    if graph.has_edge(source, target):
        return

    graph.add_edge(
        source,
        target,
        relation=relation,
        evidence=evidence,
        method=method
    )


def discover_document_relationships(graph, threats):
    """Discover document mentions and rule-based entity relationships."""

    for threat in threats:
        document_id = threat.get("id")

        if document_id not in graph:
            continue

        content = (
            str(threat.get("title", ""))
            + ". "
            + str(threat.get("content", ""))
        )

        mentioned_entities = find_entity_mentions(content, graph)

        # Link uploaded documents or records to entities they mention.
        for entity_id in mentioned_entities:
            if entity_id == document_id:
                continue

            evidence = extract_evidence(
                content,
                entity_id,
                entity_id
            )

            add_relationship(
                graph,
                document_id,
                entity_id,
                "DOCUMENT_MENTIONS",
                evidence or content[:500],
                "Rule-based entity detection"
            )

        # Look for two known entities appearing in the same sentence.
        sentences = re.split(r"(?<=[.!?])\s+", content)

        for sentence in sentences:
            sentence_entities = find_entity_mentions(sentence, graph)

            if len(sentence_entities) < 2:
                continue

            for i in range(len(sentence_entities)):
                for j in range(i + 1, len(sentence_entities)):
                    first_id = sentence_entities[i]
                    second_id = sentence_entities[j]

                    relation = infer_relationship(
                        first_id,
                        second_id,
                        sentence
                    )

                    if relation:
                        add_relationship(
                            graph,
                            first_id,
                            second_id,
                            relation,
                            sentence.strip()[:500],
                            "Rule-based relationship inference"
                        )


def build_knowledge_graph():
    """Build a cybersecurity knowledge graph."""

    graph = nx.DiGraph()

    threats = load_threats()

    # Create graph nodes.
    for threat in threats:
        graph.add_node(
            threat["id"],
            label=threat["title"],
            category=threat["category"],
            description=threat.get("content", ""),
            source=threat.get("source", "")
        )

    # Preserve the original manually defined relationships.
    relationships = [
        ("TH001", "TH002", "AFFECTS"),
        ("TH001", "TH003", "CAN_ENABLE"),
        ("TH001", "TH004", "POTENTIAL_TECHNIQUE_MAPPING")
    ]

    for source, target, relation in relationships:
        if source in graph and target in graph:
            graph.add_edge(
                source,
                target,
                relation=relation,
                evidence="Manually defined initial relationship",
                method="Seeded knowledge"
            )

    # Discover additional relationships from document content.
    discover_document_relationships(graph, threats)

    return graph


def find_related_threats(question, top_k=5):
    """Find graph entities related to a user question."""

    graph = build_knowledge_graph()
    question = normalize_text(question)

    matched_nodes = []

    for node, details in graph.nodes(data=True):
        searchable_text = (
            normalize_text(details.get("label", ""))
            + " "
            + normalize_text(details.get("description", ""))
            + " "
            + normalize_text(details.get("category", ""))
        )

        if any(
            word in searchable_text
            for word in question.split()
            if len(word) > 2
        ):
            matched_nodes.append(node)

    related_nodes = set(matched_nodes)

    for node in matched_nodes:
        related_nodes.update(graph.successors(node))
        related_nodes.update(graph.predecessors(node))

    results = []

    for node in related_nodes:
        if node in graph:
            details = graph.nodes[node]

            results.append({
                "id": node,
                "title": details["label"],
                "category": details["category"],
                "description": details["description"]
            })

    # Put direct question matches before neighbouring nodes.
    results.sort(
        key=lambda item: (
            item["id"] not in matched_nodes,
            item["title"]
        )
    )

    return results[:top_k]


def get_graph_relationships():
    """Return graph relationships with evidence and discovery method."""

    graph = build_knowledge_graph()

    return [
        {
            "source": graph.nodes[source]["label"],
            "target": graph.nodes[target]["label"],
            "relationship": details.get("relation", "RELATED_TO"),
            "method": details.get("method", "Unknown"),
            "evidence": details.get("evidence", "")
        }
        for source, target, details in graph.edges(data=True)
    ]
