FROM oxzk/debian

WORKDIR /app

COPY . .

RUN apt update && apt install git wget curl -y \
    && wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash - \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

CMD ["uv", "run", "python", "main.py"]
