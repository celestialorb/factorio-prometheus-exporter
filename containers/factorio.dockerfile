# Start from our base production Factorio container image.
FROM docker.io/factoriotools/factorio:2.0.11

# Add some local development tooling.
RUN apt update && apt install --assume-yes git gpg zsh

# Setup additional tooling for the project.
RUN apt install --assume-yes python3 python3-pip
COPY dev.requirements.txt /tmp/dev.requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages \
  --requirement /tmp/dev.requirements.txt \
  --requirement /tmp/requirements.txt

# Setup the Factorio user.
RUN curl --silent --show-error --output /tmp/starship.sh https://starship.rs/install.sh \
  && chmod a+x /tmp/starship.sh \
  && /tmp/starship.sh --version latest --yes
RUN usermod --uid 1000 factorio
RUN groupmod --gid 1000 factorio
RUN chown -R factorio:factorio /factorio /opt/factorio
RUN usermod --shell /bin/zsh factorio
RUN mkhomedir_helper factorio
USER factorio
RUN mkdir --parents ${HOME}/.config
COPY containers/tweaks.zshrc /tmp/tweaks.zshrc
RUN cat /tmp/tweaks.zshrc >> ${HOME}/.zshrc
RUN starship preset gruvbox-rainbow --output ${HOME}/.config/starship.toml

ENTRYPOINT [ "/bin/zsh" ]
