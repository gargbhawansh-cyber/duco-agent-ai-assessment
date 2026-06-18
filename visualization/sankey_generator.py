"""
Sankey Diagram Generator for Cost Flow Visualization
Creates actual rendered visualizations instead of just JSON data structures
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.sankey import Sankey
import numpy as np
from typing import Dict, Any, List, Optional
import os


class SankeyGenerator:
    """Generate actual Sankey diagram visualizations for cost flow"""
    
    def __init__(self):
        self.figure_size = (14, 10)
        self.dpi = 100
    
    def generate_sankey_diagram(
        self,
        cost_flow_data: Dict[str, Any],
        output_path: str = "outputs/cost_flow_diagram.png"
    ) -> str:
        """
        Generate a Sankey diagram from cost flow data
        
        Args:
            cost_flow_data: Cost flow data structure from Output Agent
            output_path: Path to save the generated diagram
            
        Returns:
            Path to the generated diagram
        """
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            
            # Extract nodes and links from data
            nodes = cost_flow_data.get('nodes', [])
            links = cost_flow_data.get('links', [])
            
            # Convert to Sankey format
            sankey_data = self._convert_to_sankey_format(nodes, links)
            
            # Create Sankey diagram
            sankey = Sankey(
                ax=ax,
                unit='₹',
                format=lambda x, unit: f'{x:,.0f} {unit}',
                label=None,
                scale=1.0 / max([link['value_inr'] for link in links]) if links else 1.0,
                **sankey_data
            )
            
            # Add labels
            self._add_node_labels(ax, nodes, sankey)
            
            # Add title and subtitle
            title = cost_flow_data.get('title', 'DuCO-Agent: COB Cost Flow')
            subtitle = cost_flow_data.get('subtitle', '')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            if subtitle:
                ax.text(0.5, 0.95, subtitle, transform=ax.transAxes, 
                       ha='center', va='top', fontsize=12, style='italic')
            
            # Add legend
            self._add_legend(ax, nodes)
            
            # Adjust layout
            plt.tight_layout()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save figure
            plt.savefig(output_path, bbox_inches='tight', dpi=self.dpi)
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"Error generating Sankey diagram: {e}")
            # Fallback to simple bar chart if Sankey fails
            return self._generate_fallback_chart(cost_flow_data, output_path)
    
    def _convert_to_sankey_format(self, nodes: List[Dict], links: List[Dict]) -> Dict:
        """
        Convert cost flow data to Sankey format
        
        Args:
            nodes: Node definitions
            links: Link definitions
            
        Returns:
            Sankey-compatible data dictionary
        """
        # Create node index mapping
        node_indices = {node['id']: i for i, node in enumerate(nodes)}
        
        # Prepare Sankey data
        sankey_data = {
            'orientations': [0] * len(nodes),  # All horizontal
            'patchlabel': [node['label'] for node in nodes],
            'facecolor': [node.get('color', '#1f77b4') for node in nodes],
            'edgecolor': 'none',
            'linewidth': 2.0
        }
        
        # Add flows
        flows = []
        for link in links:
            source_idx = node_indices.get(link['source'], 0)
            target_idx = node_indices.get(link['target'], 0)
            value = link['value_inr']
            
            # Add forward flow
            flows.append([source_idx, target_idx, value, link.get('label', '')])
        
        if flows:
            sankey_data['flows'] = flows
        
        return sankey_data
    
    def _add_node_labels(self, ax, nodes: List[Dict], sankey):
        """Add labels to Sankey diagram nodes"""
        # Sankey automatically adds labels, but we can customize them
        pass
    
    def _add_legend(self, ax, nodes: List[Dict]):
        """Add legend to the diagram"""
        # Create legend patches
        patches = []
        labels = []
        for node in nodes:
            color = node.get('color', '#1f77b4')
            label = node['label']
            patches.append(mpatches.Patch(color=color, label=label))
            labels.append(label)
        
        # Add legend
        if patches:
            ax.legend(patches, labels, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    def _generate_fallback_chart(
        self,
        cost_flow_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate a fallback bar chart if Sankey fails
        
        Args:
            cost_flow_data: Cost flow data
            output_path: Path to save the chart
            
        Returns:
            Path to the generated chart
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8), dpi=self.dpi)
            
            # Extract summary data
            summary = cost_flow_data.get('summary', {})
            
            # Create bar chart
            categories = ['Total Billed', 'Plan A Payment', 'Plan B Payment', 'Patient OOP']
            values = [
                summary.get('total_billed', 0),
                summary.get('plan_a_total', 0),
                summary.get('plan_b_total', 0),
                summary.get('patient_total', 0)
            ]
            colors = ['#FF6B6B', '#96CEB4', '#45B7D1', '#FFEAA7']
            
            bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'₹{value:,.0f}',
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            # Add title
            title = cost_flow_data.get('title', 'DuCO-Agent: COB Cost Flow')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # Add subtitle
            subtitle = cost_flow_data.get('subtitle', '')
            if subtitle:
                ax.text(0.5, 0.95, subtitle, transform=ax.transAxes,
                       ha='center', va='top', fontsize=12, style='italic')
            
            # Format y-axis
            ax.set_ylabel('Amount (INR)', fontsize=12, fontweight='bold')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            # Grid
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            # Tight layout
            plt.tight_layout()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save figure
            plt.savefig(output_path, bbox_inches='tight', dpi=self.dpi)
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"Error generating fallback chart: {e}")
            return output_path  # Return the path even if generation failed
    
    def generate_interactive_html(
        self,
        cost_flow_data: Dict[str, Any],
        output_path: str = "outputs/cost_flow_interactive.html"
    ) -> str:
        """
        Generate an interactive HTML visualization using Plotly
        
        Args:
            cost_flow_data: Cost flow data structure
            output_path: Path to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        try:
            import plotly.graph_objects as go
            
            # Extract nodes and links
            nodes = cost_flow_data.get('nodes', [])
            links = cost_flow_data.get('links', [])
            
            # Create node list for Plotly
            node_labels = [node['label'] for node in nodes]
            node_colors = [node.get('color', '#1f77b4') for node in nodes]
            
            # Create link list for Plotly
            link_sources = [nodes.index(next(n for n in nodes if n['id'] == link['source'])) 
                           for link in links]
            link_targets = [nodes.index(next(n for n in nodes if n['id'] == link['target'])) 
                           for link in links]
            link_values = [link['value_inr'] for link in links]
            link_labels = [link.get('label', '') for link in links]
            
            # Create Sankey diagram
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color='black', width=0.5),
                    label=node_labels,
                    color=node_colors
                ),
                link=dict(
                    source=link_sources,
                    target=link_targets,
                    value=link_values,
                    label=link_labels,
                    line=dict(color='black', width=0.5),
                    color='rgba(0,0,0,0.2)'
                )
            )])
            
            # Add title
            title = cost_flow_data.get('title', 'DuCO-Agent: COB Cost Flow')
            subtitle = cost_flow_data.get('subtitle', '')
            fig.update_layout(
                title_text=f"<b>{title}</b><br><sub>{subtitle}</sub>",
                font_size=12,
                height=600
            )
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save HTML
            fig.write_html(output_path)
            
            return output_path
            
        except ImportError:
            print("Plotly not installed, skipping interactive HTML generation")
            return None
        except Exception as e:
            print(f"Error generating interactive HTML: {e}")
            return None
