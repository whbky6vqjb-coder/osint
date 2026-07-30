# Skill : Investigation d'une Entreprise (Personne Morale)

Ce protocole décrit la démarche méthodologique standard pour investiguer une entité corporative ou un numéro SIRET/SIREN.

## Démarche Méthodologique

1. **Phase 1 : Identification Légale**
   - Lancer l'outil `insee_sirene_lookup` ou `gleif_lei_lookup` pour valider l'existence légale de la structure.
   - Si la cible est hors de France, utiliser `opencorporates_search`.
   
2. **Phase 2 : Analyse Offshore et Sanctions**
   - Interroger le registre `icij_offshore_leaks` pour chercher d'éventuels montages dans des paradis fiscaux.
   - Lancer une vérification via `open_sanctions_check` pour vérifier la présence de l'entité ou de ses dirigeants sur des listes de gel des avoirs.

3. **Phase 3 : Analyse des Infrastructures**
   - Récupérer les domaines web enregistrés liés à la marque et vérifier leur historique WHOIS.
   - Extraire les adresses email professionnelles associées pour déceler des fuites de données d'identifiants via `breach_check`.

4. **Phase 4 : Corrélation & Analyse de Preuve**
   - Croiser les adresses postales de filiales avec les données d'autres entreprises déclarées à la même adresse (risque d'entreprises boîtes aux lettres).
   - Compiler l'ensemble des résultats via le Forensic Tracker pour générer les hashes SHA-256.
