FROM python:3.11.4
WORKDIR /app

COPY . /app

# RUN mkdir ~/.streamlit
# RUN cp .streamlit/config.toml ~/.streamlit/config.toml
RUN pip install -r requirements.txt
