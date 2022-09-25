FROM python:3.8

COPY requirements.txt requirements.txt
COPY app app
COPY setup.py setup.py

# install requires
RUN pip install -r requirements.txt

# go
CMD ["python", "-m", "app.wsgi"]
# CMD ["bash"]
