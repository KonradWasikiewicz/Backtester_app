from flask import Flask, request, jsonify
import traceback

app = Flask(__name__)

@app.route('/runBrowserAction', methods=['POST'])
def run_browser_action():
    params = request.json or {}
    result = {}
    try:
        # Removed: browser action script no longer used
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    # Run on port 3001 to serve ChatGPT function calls
    app.run(host='0.0.0.0', port=3001)
