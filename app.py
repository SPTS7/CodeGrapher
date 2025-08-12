from flask import Flask, render_template, request, jsonify
from pathlib import Path
import analyzer_lib as analyzer

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_code():
    data = request.json
    project_dir = data.get('projectDir')
    entry_file = data.get('entryFile')
    entry_func = data.get('entryFunc')
    api_key = data.get('apiKey')
    use_ai = api_key is not None and api_key != ''
    
    if not project_dir or not Path(project_dir).is_dir():
        return jsonify({'error': 'Invalid or missing project directory.'}), 400
    if not entry_file:
        return jsonify({'error': 'Entry file is required.'}), 400

    all_funcs, logs = analyzer.analyze_project(project_dir)
    
    entry_points = []
    if entry_func:
        if entry_func in all_funcs:
            entry_points.append(entry_func)
        else:
            return jsonify({'error': f"Entry function '{entry_func}' not found."}), 400
    else:
        entry_file_path = str(Path(project_dir) / entry_file)
        entry_points = [name for name, data in all_funcs.items() if Path(data['file_path']).resolve() == Path(entry_file_path).resolve()]

    if not entry_points:
        return jsonify({'error': f'No functions found for the specified entry point.'}), 400
        
    call_graph = analyzer.build_call_graph(all_funcs, entry_points)
    
    if use_ai:
        ai_logs = analyzer.enrich_with_ai_summaries(call_graph, api_key)
        logs.extend(ai_logs)
    
    # Generate data for the interactive diagram
    diagram_data = analyzer.generate_interactive_diagram_data(call_graph)
    logs.append("\nInteractive diagram data generated.")
    
    return jsonify({
        'logs': "\n".join(logs),
        'diagramData': diagram_data
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
