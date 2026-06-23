from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template('index.html', protests=[])
    except Exception as e:
        import traceback
        return f'<pre>Error: {str(e)}\n{traceback.format_exc()}</pre>'

if __name__ == '__main__':
    app.run(debug=True, port=5004)
