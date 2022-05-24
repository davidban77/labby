ARG PYTHON_VER
FROM python:${PYTHON_VER}-slim as labby-base

USER 0

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1 \
    LABBY_ROOT=/opt/labby

# Upgrade and install system's dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends vim git openssh-client telnet && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* && \
    pip --no-cache-dir install --upgrade pip wheel

# Generate required dirs for later consumption
RUN mkdir /opt/labby

# -------------------------------------------------------------------------------------
# Development Image
# -------------------------------------------------------------------------------------
FROM python:${PYTHON_VER} as labby-dev

# Upgrade and install system's dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends gcc gcc-multilib && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* && \
    pip --no-cache-dir install --upgrade pip wheel


RUN pip install poetry

COPY . /source

# Install dependencies
SHELL ["/bin/bash", "-c"]
RUN cd /source && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi && \
    mkdir /tmp/dist && \
    poetry export --without-hashes -o /tmp/dist/requirements.txt

WORKDIR /source

# Generate labby wheel
RUN poetry build

# -------------------------------------------------------------------------------------
# Final Image
# -------------------------------------------------------------------------------------
FROM labby-base as labby
ARG PYTHON_VER

# Copy necessary dependencies and wheel from dev phase
COPY --from=labby-dev /usr/local/lib/python${PYTHON_VER}/site-packages /usr/local/lib/python${PYTHON_VER}/site-packages
COPY --from=labby-dev /usr/local/bin /opt/labby/.local/bin
COPY --from=labby-dev /source/dist/*.whl /tmp

# Create labby's user to not use root
RUN useradd --system --shell /bin/bash --create-home --home-dir /opt/labby labby && \
    chown -R labby:labby /opt/labby /tmp/*.whl

USER labby

WORKDIR /opt/labby

# Install labby
RUN pip install --no-deps --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

ENV PATH="/opt/labby/.local/bin:${PATH}"
