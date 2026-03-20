from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "TFS AgentCore Test"})

@app.route('/invoke', methods=['POST'])
def invoke():
    try:
        data = request.get_json()
        input_text = data.get('prompt', data.get('inputText', ''))
        
        if not input_text:
            return jsonify({"outputText": "No input provided"})
        
        # Simple test response
        response = f"TFS AgentCore received: {input_text}"
        return jsonify({"outputText": response})
        
    except Exception as e:
        return jsonify({"outputText": f"Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
