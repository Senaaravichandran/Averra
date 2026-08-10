"""Compatibility entrypoint for Averra's application factory."""

from backend.averra import create_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["ENVIRONMENT"] == "development", port=5050)
