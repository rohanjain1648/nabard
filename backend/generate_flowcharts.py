import graphviz
import os

def create_system_overview():
    dot = graphviz.Digraph('System_Overview', comment='CashFlow Sahayak System Overview')
    dot.attr(rankdir='TB', size='10,8')

    with dot.subgraph(name='cluster_client') as c:
        c.attr(label='Client (PWA: React + Vite)', style='filled', color='lightgrey')
        c.node('UI_E', 'Enterprise Views\n(entry, forecast, alerts)', shape='box')
        c.node('UI_F', 'Field-officer Views\n(portfolio, profile, risk panel)', shape='box')
        c.node('SW', 'Service Worker\n(cache, background sync)', shape='component')
        c.node('IDB', 'IndexedDB\nlocal ledger + cached\nforecasts/alerts', shape='cylinder')
        c.node('RULES', 'Local Rule Engine\n(offline alert checks)', shape='diamond')
        
        c.edge('UI_E', 'SW')
        c.edge('UI_F', 'SW')
        c.edge('SW', 'IDB')
        c.edge('IDB', 'RULES')

    with dot.subgraph(name='cluster_api') as c:
        c.attr(label='API Backend (FastAPI)', style='filled', color='lightblue')
        c.node('AUTH', 'Auth (JWT)', shape='box')
        c.node('LEDGER', 'Ledger Service\n(entries, sync endpoint)', shape='box')
        c.node('ENT', 'Enterprise Service', shape='box')
        c.node('FORE', 'Forecast Service', shape='box')
        c.node('RISK', 'Risk & Alert Service', shape='box')
        c.node('SUGG', 'Suggestion Engine', shape='box')

    with dot.subgraph(name='cluster_ml') as c:
        c.attr(label='ML Pipeline (Python, Batch)', style='filled', color='lightgreen')
        c.node('FEAT', 'Feature Builder\n(lags, rolls, seasonality, external joins)', shape='box')
        c.node('FCST', 'Forecaster\nLightGBM quantile (P10/50/90)', shape='box')
        c.node('SCORE', 'Risk Scorer\nGBM classifier + SHAP drivers', shape='box')
        
        c.edge('FEAT', 'FCST')
        c.edge('FCST', 'SCORE')

    with dot.subgraph(name='cluster_data') as c:
        c.attr(label='Data Layer', style='filled', color='wheat')
        c.node('PG', 'PostgreSQL / SQLite', shape='cylinder')
        c.node('SIM', 'Data Simulator\n(enterprises, ledgers, shocks)', shape='box')
        c.node('EXT', 'External-signal Adapters\n(commodity, weather, UPI)', shape='box')
        
        c.edge('SIM', 'PG')
        c.edge('EXT', 'PG')

    # Cross-cluster edges
    dot.edge('SW', 'LEDGER', label='sync (batched, resumable)')
    dot.edge('UI_E', 'AUTH')
    dot.edge('UI_F', 'AUTH')
    
    dot.edge('LEDGER', 'PG')
    dot.edge('ENT', 'PG')
    dot.edge('FORE', 'PG')
    dot.edge('RISK', 'PG')
    
    dot.edge('PG', 'FEAT')
    
    dot.edge('SCORE', 'RISK', label='scores + drivers')
    dot.edge('FCST', 'FORE', label='forecast rows')
    dot.edge('RISK', 'SUGG')

    return dot


def create_data_flow():
    dot = graphviz.Digraph('Data_Flow', comment='CashFlow Sahayak Data Flow')
    dot.attr(rankdir='LR', size='12,6')
    
    dot.node('A', 'Owner logs entries\noffline', shape='box', style='filled', fillcolor='lightgrey')
    dot.node('B', 'IndexedDB', shape='cylinder')
    dot.node('C', 'Connectivity returns', shape='diamond')
    dot.node('D', 'Service Worker syncs batch', shape='box')
    dot.node('E', 'Ledger Service\npersists (idempotent)', shape='box', style='filled', fillcolor='lightblue')
    dot.node('F', 'ML Job\n(sync triggers or nightly)', shape='box', style='filled', fillcolor='lightgreen')
    dot.node('G', 'Forecast, Score, Drivers\nwritten to DB', shape='cylinder')
    dot.node('H', 'Sync response / poll', shape='box')
    dot.node('I', 'Cached client-side', shape='cylinder')
    dot.node('J', 'Officer Dashboard', shape='box', style='filled', fillcolor='lightgrey')
    
    dot.edge('A', 'B')
    dot.edge('B', 'C')
    dot.edge('C', 'D')
    dot.edge('D', 'E')
    dot.edge('E', 'F', label='triggers')
    dot.edge('F', 'G')
    dot.edge('G', 'H', label='delivers')
    dot.edge('E', 'H', label='response')
    dot.edge('H', 'I')
    dot.edge('G', 'J', label='reads aggregated\nacross portfolio')
    
    return dot


if __name__ == '__main__':
    os.makedirs('flowcharts', exist_ok=True)
    
    sys_overview = create_system_overview()
    sys_overview.render('flowcharts/system_overview', format='png', cleanup=True)
    sys_overview.render('flowcharts/system_overview', format='svg', cleanup=True)
    print("Generated flowcharts/system_overview.png and .svg")
    
    data_flow = create_data_flow()
    data_flow.render('flowcharts/data_flow', format='png', cleanup=True)
    data_flow.render('flowcharts/data_flow', format='svg', cleanup=True)
    print("Generated flowcharts/data_flow.png and .svg")
    print("Graphviz flowcharts generated successfully!")
