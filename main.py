"""Entry point for ThaiLawOnline Chatbot."""

import uvicorn


def main():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    main()
