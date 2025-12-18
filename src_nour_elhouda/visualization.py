# src/visualization.py
"""
Module de visualisation pour les résultats du flux à coût minimum.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def visualize_network(nodes, arcs, flows, title="Réseau de Transferts Financiers"):
    """
    Visualise le réseau avec les flux optimaux.
    
    Args:
        nodes: Liste des nœuds
        arcs: Liste des arcs avec capacités
        flows: Dictionnaire des flux optimaux {(source, dest): valeur}
        title: Titre du graphique
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. Graphe du réseau
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    
    # Ajouter les arcs avec leurs flux
    edge_widths = []
    edge_labels = {}
    
    for arc in arcs:
        source = arc['source']
        dest = arc['destination']
        flow = flows.get((source, dest), 0)
        
        if flow > 0:
            G.add_edge(source, dest, weight=flow)
            edge_widths.append(flow / 100000)  # Échelle pour la visualisation
            
            # Label avec flux et capacité
            capacity = arc.get('capacity', 0)
            usage = (flow / capacity * 100) if capacity > 0 else 0
            edge_labels[(source, dest)] = f"{flow:,.0f}\n({usage:.1f}%)"
    
    # Positionnement
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Tracer le graphe
    nx.draw_networkx_nodes(G, pos, ax=ax1, node_color='lightblue', 
                          node_size=1500, alpha=0.8)
    nx.draw_networkx_labels(G, pos, ax=ax1, font_size=10, font_weight='bold')
    
    # Tracer les arêtes avec largeur proportionnelle au flux
    if edge_widths:
        max_width = max(edge_widths)
        edge_widths = [w / max_width * 5 for w in edge_widths]
    
    nx.draw_networkx_edges(G, pos, ax=ax1, width=edge_widths, 
                          edge_color='#2196F3', arrows=True, arrowsize=20)
    
    # Ajouter les labels des arêtes
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                ax=ax1, font_color='red', font_size=8)
    
    ax1.set_title("Graphe des Flux", fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    # 2. Diagramme à barres des flux
    if flows:
        flow_data = []
        for (source, dest), flow in sorted(flows.items(), key=lambda x: x[1], reverse=True)[:10]:
            flow_data.append({
                'Arc': f"{source}→{dest}",
                'Flux': flow
            })
        
        df = pd.DataFrame(flow_data)
        colors = plt.cm.YlOrRd(np.linspace(0.4, 0.9, len(df)))
        
        bars = ax2.barh(df['Arc'], df['Flux'], color=colors)
        ax2.set_xlabel('Montant (€)')
        ax2.set_title('Top 10 des Flux', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            width = bar.get_width()
            ax2.text(width * 1.01, bar.get_y() + bar.get_height()/2,
                    f'{width:,.0f}', va='center', fontsize=9)
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig

def plot_flow_distribution(flows, capacity_data=None):
    """
    Trace la distribution des flux.
    
    Args:
        flows: Dictionnaire des flux
        capacity_data: Dictionnaire des capacités par arc
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Histogramme des flux
    if flows:
        flow_values = list(flows.values())
        axes[0, 0].hist(flow_values, bins=20, edgecolor='black', alpha=0.7)
        axes[0, 0].set_xlabel('Montant du Flux (€)')
        axes[0, 0].set_ylabel('Fréquence')
        axes[0, 0].set_title('Distribution des Flux')
        axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Taux d'utilisation des capacités
    if capacity_data and flows:
        usage_rates = []
        for (source, dest), flow in flows.items():
            capacity = capacity_data.get((source, dest), 1)
            if capacity > 0:
                usage_rates.append(flow / capacity * 100)
        
        if usage_rates:
            axes[0, 1].boxplot(usage_rates)
            axes[0, 1].set_ylabel('Taux d\'Utilisation (%)')
            axes[0, 1].set_title('Distribution des Taux d\'Utilisation')
            axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Flux cumulé
    if flows:
        sorted_flows = sorted(flows.values(), reverse=True)
        cum_flows = np.cumsum(sorted_flows) / sum(sorted_flows) * 100
        
        axes[1, 0].plot(range(1, len(cum_flows) + 1), cum_flows, marker='o')
        axes[1, 0].set_xlabel('Nombre d\'Arcs (triés)')
        axes[1, 0].set_ylabel('Flux Cumulé (%)')
        axes[1, 0].set_title('Courbe de Lorenz des Flux')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Ligne de référence (égalité parfaite)
        axes[1, 0].plot([1, len(cum_flows)], [0, 100], 'r--', alpha=0.5)
    
    # 4. Diagramme circulaire des flux par source
    if flows:
        source_totals = {}
        for (source, _), flow in flows.items():
            source_totals[source] = source_totals.get(source, 0) + flow
        
        if source_totals:
            labels = list(source_totals.keys())
            sizes = list(source_totals.values())
            
            wedges, texts, autotexts = axes[1, 1].pie(
                sizes, 
                labels=labels, 
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.Set3(np.linspace(0, 1, len(labels)))
            )
            
            axes[1, 1].set_title('Répartition des Flux par Source')
    
    plt.suptitle('Analyse des Flux Optimaux', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    return fig

def plot_interactive_network(nodes, arcs, flows):
    """
    Crée une visualisation interactive avec Plotly.
    
    Args:
        nodes: Liste des nœuds
        arcs: Liste des arcs
        flows: Dictionnaire des flux
    """
    # Créer le graphe
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    
    # Ajouter les arcs avec les flux
    for arc in arcs:
        source = arc['source']
        dest = arc['destination']
        flow = flows.get((source, dest), 0)
        
        if flow > 0:
            G.add_edge(source, dest, weight=flow)
    
    # Positionnement
    pos = nx.spring_layout(G)
    
    # Préparer les données pour Plotly
    edge_trace = []
    node_trace = go.Scatter(
        x=[pos[node][0] for node in nodes],
        y=[pos[node][1] for node in nodes],
        mode='markers+text',
        text=nodes,
        textposition="top center",
        marker=dict(
            size=20,
            color='lightblue',
            line=dict(color='black', width=2)
        ),
        name='Banques/Comptes'
    )
    
    # Tracer les arêtes
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = edge[2]['weight']
        
        edge_trace.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=weight/10000, color='#888'),
                hoverinfo='text',
                text=f"Flux: {weight:,.0f} €",
                name=f"{edge[0]} → {edge[1]}"
            )
        )
    
    # Créer la figure
    fig = go.Figure(data=edge_trace + [node_trace])
    
    # Mise en page
    fig.update_layout(
        title='Réseau de Transferts Financiers (Interactif)',
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

def plot_results_comparison(scenarios, costs):
    """
    Compare les coûts de différents scénarios.
    
    Args:
        scenarios: Liste des noms des scénarios
        costs: Liste des coûts correspondants
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(scenarios, costs, color=['#4CAF50', '#FF9800', '#2196F3', '#9C27B0'])
    
    # Ajouter les valeurs
    for bar, cost in zip(bars, costs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{cost:,.0f} €', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Coût Total (€)', fontweight='bold')
    ax.set_title('Comparaison des Stratégies de Transfert', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Améliorer les ticks
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    return fig

def create_heatmap(flows, nodes):
    """
    Crée une carte thermique des flux entre nœuds.
    
    Args:
        flows: Dictionnaire des flux
        nodes: Liste des nœuds
    """
    # Créer une matrice de flux
    n = len(nodes)
    flow_matrix = np.zeros((n, n))
    
    # Remplir la matrice
    node_index = {node: i for i, node in enumerate(nodes)}
    for (source, dest), flow in flows.items():
        if source in node_index and dest in node_index:
            i = node_index[source]
            j = node_index[dest]
            flow_matrix[i, j] = flow
    
    # Créer la figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Créer la carte thermique
    im = ax.imshow(flow_matrix, cmap='YlOrRd', aspect='auto')
    
    # Ajouter les annotations
    for i in range(n):
        for j in range(n):
            if flow_matrix[i, j] > 0:
                ax.text(j, i, f'{flow_matrix[i, j]:,.0f}',
                       ha='center', va='center', color='black', fontsize=8)
    
    # Configurer les axes
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(nodes, rotation=45, ha='right')
    ax.set_yticklabels(nodes)
    ax.set_xlabel('Destination', fontweight='bold')
    ax.set_ylabel('Source', fontweight='bold')
    ax.set_title('Carte Thermique des Flux Interbancaires', fontsize=14, fontweight='bold')
    
    # Ajouter une barre de couleur
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Montant (€)', fontweight='bold')
    
    plt.tight_layout()
    return fig