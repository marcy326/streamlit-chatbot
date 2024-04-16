# Streamlit ChatBot App

This is a simple chatbot application built with Streamlit, which allows users to interact with a language model (LLM) powered by either OpenAI or Anthropic.

## Features

- Users can start new conversations or load existing ones from the history.
- The chatbot responds to user input in real-time using the selected language model.
- Conversations can be summarized and saved for later reference.

## Prerequisites

Before running the application, make sure you have the following installed:

- Python 3
- Docker (optional, for containerization)

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/marcy326/streamlit-chatbot.git
cd streamlit-chatbot-app
```

## Usage
To run the application locally, execute the following command:

```bash
docker compose up --build
```
This command will build the Docker image and start the application container. You can access the deployed application at http://localhost:8501.

## Configuration

Before running the application, create a `.env` file in the root directory of the project and define the following environment variables:

```dotenv
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```
Additionally, you can customize the following options in the config.py file:

DEFAULT_TITLE: The title of the application.
USER_NAME: The name displayed for user messages in the chat.
ASSISTANT_NAME: The name displayed for assistant (bot) messages in the chat.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

This application was built using the Streamlit library (https://streamlit.io/).
The language model integration was achieved using the OpenAI API (https://openai.com/) and the Anthropic API (https://www.anthropic.com/).