# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:45:49 2025

@author: msi
"""
    self.results_text.append("\n📈 ANALYSE DE SENSIBILITÉ (Prix duaux):")
    self.results_text.append("="*60)
    
    if result.ombre_prix and len(result.ombre_prix) > 0:
        # Grouper par type de contrainte
        contraintes_actives = {}
        
        for nom, prix in result.ombre_prix.items():
            # Identifier le type
            if 'quantite_totale' in nom:
                type_ = "QUANTITÉ TOTALE"
                interpretation = f"Coût marginal de production: {prix:.4f} €/kg"
                contraintes_actives[type_] = (nom, prix, interpretation)
            
            elif 'palatabilite' in nom:
                type_ = "PALATABILITÉ"
                interpretation = f"Coût pour améliorer le goût: {prix:.4f} €/unité"
                contraintes_actives[type_] = (nom, prix, interpretation)
            
            elif 'min_' in nom:
                nutriment = nom.replace('min_', '')
                type_ = f"MIN {nutriment.upper()}"
                interpretation = f"Coût de l'exigence minimale: {prix:.4f} €/g"
                contraintes_actives[type_] = (nom, prix, interpretation)
            
            elif 'max_' in nom:
                nutriment = nom.replace('max_', '')
                type_ = f"MAX {nutriment.upper()}"
                interpretation = f"Gain si on relâche la limite: {-prix:.4f} €/g"
                contraintes_actives[type_] = (nom, prix, interpretation)
            
            elif 'glucides_ratio' in nom or 'lipides_ratio' in nom:
                type_ = "BALANCE ÉNERGÉTIQUE"
                interpretation = f"Coût du ratio: {prix:.4f} €/%"
                contraintes_actives[type_] = (nom, prix, interpretation)
        
        # Afficher de façon organisée
        self.results_text.append("\n🔍 CONTRAINTES ACTIVES (liantes):")
        self.results_text.append("-"*40)
        
        for type_, (nom, prix, interpretation) in contraintes_actives.items():
            self.results_text.append(f"  {type_:25} {prix:8.4f} €/unit")
            self.results_text.append(f"     → {interpretation}")
        
        self.results_text.append(f"\n  Total: {len(contraintes_actives)} contrainte(s) active(s)")
        
    else:
        self.results_text.append("\n⚠️  AUCUNE CONTRAINTE ACTIVE")
        self.results_text.append("-"*40)
        self.results_text.append("Toutes les contraintes sont non-liantes (relâchables sans coût)")
        self.results_text.append("→ La solution est à l'intérieur de tous les intervalles")
    
    # SECTION CONTRAINTES NON ACTIVES
    self.results_text.append("\n🔍 CONTRAINTES NON ACTIVES (non liantes):")
    self.results_text.append("-"*40)
    
    # Lister les contraintes nutritionnelles qui pourraient être actives
    contraintes_nutrition = ['proteines', 'lipides', 'glucides', 'fibres', 'calcium', 'phosphore']
    
    for nut in contraintes_nutrition:
        min_active = f"min_{nut}" in [c for c in result.ombre_prix.keys()] if result.ombre_prix else False
        max_active = f"max_{nut}" in [c for c in result.ombre_prix.keys()] if result.ombre_prix else False
        
        if not min_active and not max_active:
            # Vérifier la valeur actuelle
            valeur = result.valeurs_nutritionnelles.get(nut, 0)
            
            # Trouver les bornes (à partir de votre interface)
            # Pour l'exemple, on met des bornes fictives
            min_borne = 0
            max_borne = 1000
            
            if valeur > min_borne + 10 and valeur < max_borne - 10:
                self.results_text.append(f"  {nut:15} : {valeur:6.1f} g/kg (loin des bornes)")
            else:
                self.results_text.append(f"  {nut:15} : {valeur:6.1f} g/kg")
    
    # SECTION INTERPRÉTATION
    self.results_text.append("\n💡 INTERPRÉTATION:")
    self.results_text.append("-"*40)
    
    if result.ombre_prix and 'quantite_totale' in result.ombre_prix:
        prix = result.ombre_prix['quantite_totale']
        self.results_text.append(f"• Coût marginal de production: {prix:.3f} €/kg")
        self.results_text.append(f"  → Produire 1 kg de plus coûterait {prix:.3f} €")
    
    if result.ombre_prix and any('palatabilite' in k for k in result.ombre_prix.keys()):
        for k, v in result.ombre_prix.items():
            if 'palatabilite' in k:
                self.results_text.append(f"• Améliorer le goût coûte: {v:.3f} €/unité d'indice")
                self.results_text.append(f"  → Rendre +1 unité plus sucré coûte {v:.3f} €")
                break
    
    self.results_text.append("\n📊 RÉSUMÉ DES COÛTS RÉDUITS:")
    self.results_text.append("-"*40)
    
    if result.couts_reduits and len(result.couts_reduits) > 0:
        # Ingrédients NON utilisés mais intéressants
        ingredients_non_utilises = []
        
        for nom, cout in result.couts_reduits.items():
            if nom.startswith('x_') and cout > 0.01:  # Seuil significatif
                ing_nom = nom[2:].replace('_', ' ')
                ingredients_non_utilises.append((ing_nom, cout))
        
        if ingredients_non_utilises:
            self.results_text.append("Ingrédients qui deviendraient intéressants si moins chers:")
            for ing_nom, cout in sorted(ingredients_non_utilises, key=lambda x: x[1]):
                self.results_text.append(f"  • {ing_nom:20} : -{cout:.3f} €/kg")
                self.results_text.append(f"    (actuellement trop cher de {cout:.3f} €/kg)")
        else:
            self.results_text.append("Tous les ingrédients intéressants sont déjà utilisés")
    else:
        self.results_text.append("Solution dégénérée ou toutes variables en base")        