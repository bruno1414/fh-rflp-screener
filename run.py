from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting FH RFLP Screener...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, port=5000)