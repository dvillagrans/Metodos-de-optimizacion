from app import create_app

app = create_app()

if __name__ == '__main__':
    # Habilitar debug=True para auto-reload automático
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
