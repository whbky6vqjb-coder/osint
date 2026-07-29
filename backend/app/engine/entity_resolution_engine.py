import re
from rapidfuzz import fuzz
from typing import Dict, Any, List, Set

LEGAL_SUFFIXES_REGEX = re.compile(r'\b(s\.?a\.?s\.?|s\.?a\.?|ltd\.?|llc\.?|inc\.?|gmbh|corp\.?|corporation|limited)\b', re.IGNORECASE)

class EntityResolutionEngine:
    """Moteur de Résolution d'Entités & Fusion d'Identités (Entity Resolution Engine)
    Optimisé pour 4 vCPU avec nettoyage de suffixes juridiques (Blocking Candidates) et RapidFuzz C++.
    """

    @staticmethod
    def normalize_legal_name(name: str) -> str:
        """Nettoie les suffixes juridiques institutionnels pour maximiser la précision de comparaison"""
        if not name:
            return ""
        cleaned = LEGAL_SUFFIXES_REGEX.sub("", name)
        return re.sub(r'\s+', ' ', cleaned).strip().lower()

    @staticmethod
    def calculate_probabilistic_match(entity1: Dict[str, Any], entity2: Dict[str, Any]) -> float:
        """Calcule la probabilité d'identité entre deux enregistrements d'entités (0.0 à 1.0)"""
        score = 0.0
        weights_sum = 0.0

        # Match sur le Nom / Libellé avec nettoyage de forme juridique (Poids: 40%)
        label1 = EntityResolutionEngine.normalize_legal_name(str(entity1.get("label", "")))
        label2 = EntityResolutionEngine.normalize_legal_name(str(entity2.get("label", "")))
        if label1 and label2:
            name_score = fuzz.token_sort_ratio(label1, label2) / 100.0
            score += name_score * 0.4
            weights_sum += 0.4

        # Match sur l'Email / Contact (Poids: 30%)
        email1 = entity1.get("email")
        email2 = entity2.get("email")
        if email1 and email2:
            email_score = 1.0 if email1.lower() == email2.lower() else 0.0
            score += email_score * 0.3
            weights_sum += 0.3

        # Match sur le SIREN / LEI / Numéro d'immatriculation (Poids: 30%)
        reg1 = entity1.get("registration_num")
        reg2 = entity2.get("registration_num")
        if reg1 and reg2:
            reg_score = 1.0 if str(reg1).strip() == str(reg2).strip() else 0.0
            score += reg_score * 0.3
            weights_sum += 0.3

        final_probability = (score / weights_sum) if weights_sum > 0 else 0.0
        return round(final_probability, 3)

    @staticmethod
    def cluster_and_resolve_entities(nodes_list: List[Dict[str, Any]], threshold: float = 0.82) -> List[Dict[str, Any]]:
        """Dédoublonne et fusionne les entités en clusters d'identités uniques avec blocage candidat"""
        resolved_clusters = []
        visited_ids: Set[str] = set()

        for i, node1 in enumerate(nodes_list):
            node_id1 = str(node1.get("id"))
            if node_id1 in visited_ids:
                continue

            cluster = {
                "master_id": f"cluster-{node_id1}",
                "canonical_name": node1.get("label"),
                "primary_type": node1.get("type", "Entity"),
                "aliases": [node1.get("label")],
                "member_node_ids": [node_id1],
                "attributes": node1.copy()
            }
            visited_ids.add(node_id1)

            for j in range(i + 1, len(nodes_list)):
                node2 = nodes_list[j]
                node_id2 = str(node2.get("id"))
                if node_id2 in visited_ids:
                    continue

                prob = EntityResolutionEngine.calculate_probabilistic_match(node1, node2)
                if prob >= threshold:
                    cluster["member_node_ids"].append(node_id2)
                    if node2.get("label") not in cluster["aliases"]:
                        cluster["aliases"].append(node2.get("label"))
                    visited_ids.add(node_id2)

            resolved_clusters.append(cluster)

        return resolved_clusters
