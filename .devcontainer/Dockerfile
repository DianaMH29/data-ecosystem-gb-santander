FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl unzip git nano wget sudo make && \
    rm -rf /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd -m -s /bin/bash --uid ${USER_UID} --gid ${USER_GID} ${USERNAME} && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME}

RUN python -m pip install --upgrade pip setuptools build

WORKDIR /workspaces/data-ecosystem-gb-santander
USER ${USERNAME}
