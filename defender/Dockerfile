FROM python:3.9

#############################
# INSTALL PYTHON DEPENDENCIES
#############################

# install git for pip install git+https:// and build tools
RUN apt-get -o Acquire::Max-FutureTime=100000 update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*

# create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# copy and install python requirements + ember from github
COPY docker-requirements.txt .
RUN pip install --no-cache-dir -r docker-requirements.txt \
 && pip install --no-cache-dir git+https://github.com/elastic/ember.git

#############################
# REBASE & DEPLOY CODE
#############################

# rebase to make a smaller image
FROM python:3.9

# required libgomp1 for ember
RUN apt-get -o Acquire::Max-FutureTime=100000 update \
    && apt-get -y --no-install-recommends install \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# copy python virtual env (all dependencies) from previous image
COPY --from=0 /opt/venv /opt/venv

# copy defender code (this directory) to /opt/defender/defender
COPY . /opt/defender/defender

#############################
# SETUP ENVIRONMENT
#############################

# open port 8080 (competition requirement)
EXPOSE 8080

# add a defender user and switch user
RUN groupadd -r defender && useradd --no-log-init -r -g defender defender
USER defender

# change working directory
WORKDIR /opt/defender/

# update environmental variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/defender"
ENV PORT=8080

#############################
# RUN CODE
#############################
CMD ["python","-m","defender"]


