import re
from typing import Dict, Any, List

class NATDisambiguationEngine:
    """
    Moteur de détection des réseaux partagés (CGNAT / NAT / Wi-Fi / Proxy)
    et de prévention des faux positifs lors de la corrélation d'identités réseau.
    """
    
    CGNAT_PREFIXES = ("100.64.", "100.65.", "100.66.", "100.67.", "100.68.", "100.69.", "100.70.", "100.71.")
    PRIVATE_NAT_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "192.168.")
    
    @classmethod
    def evaluate_network_identity_risk(cls, ip_address: str, client_anchors: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calcule la certitude et le risque de faux positif pour une adresse IP donnée.
        Empêche toute fausse attribution basée uniquement sur une IP publique partagée.
        """
        client_anchors = client_anchors or {}
        ip_clean = ip_address.strip()
        
        is_cgnat = ip_clean.startswith(cls.CGNAT_PREFIXES)
        is_private_nat = ip_clean.startswith(cls.PRIVATE_NAT_PREFIXES)
        is_shared_network = is_cgnat or is_private_nat or ("mobile" in ip_clean.lower())
        
        # Ancreurs secondaires requis pour valider une identité
        valid_anchors = []
        if client_anchors.get("adint_analytics_id"):
            valid_anchors.append("ADINT_ANALYTICS_CROSS_LINK")
        if client_anchors.get("tls_ja3_ja4_fingerprint"):
            valid_anchors.append("TLS_JA4_FINGERPRINT")
        if client_anchors.get("user_agent_device_hash"):
            valid_anchors.append("DEVICE_CANVAS_HASH")

        anchors_count = len(valid_anchors)
        
        # Calcul du score de confiance et risque de faux positif
        if is_shared_network and anchors_count < 2:
            false_positive_risk = "HIGH"
            confidence_score = 15.0
            status_message = "IP partagée (CGNAT/NAT). Corrélation impossible sur l'IP seule sans ancreurs ADINT/TLS."
        elif anchors_count >= 2:
            false_positive_risk = "LOW"
            confidence_score = 92.5
            status_message = f"Identité confirmée via {anchors_count} ancreurs secondaires (ADINT/TLS/Device)."
        else:
            false_positive_risk = "MEDIUM"
            confidence_score = 55.0
            status_message = "IP unique mais ancreurs secondaires manquants. Risque modéré."

        return {
            "target_ip": ip_clean,
            "is_shared_network": is_shared_network,
            "network_type": "CGNAT_CARRIER_GRADE_NAT" if is_cgnat else ("PRIVATE_NAT" if is_private_nat else "PUBLIC_IP"),
            "anchors_validated": valid_anchors,
            "anchors_count": anchors_count,
            "false_positive_risk": false_positive_risk,
            "confidence_score": confidence_score,
            "status_message": status_message
        }
