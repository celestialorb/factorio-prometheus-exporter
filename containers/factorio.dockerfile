# Start from our base production Factorio container image.
FROM docker.io/factoriotools/factorio:2.0.11

# Add some local development tooling.
RUN apt update && apt install --assume-yes git gpg zsh
RUN curl --silent --show-error --output /tmp/starship.sh https://starship.rs/install.sh \
  && chmod a+x /tmp/starship.sh \
  && /tmp/starship.sh --version latest --yes
RUN usermod --uid 1000 factorio
RUN groupmod --gid 1000 factorio
RUN chown -R factorio:factorio /factorio /opt/factorio
RUN usermod --shell /bin/zsh factorio

# Setup the Factorio user.
RUN mkhomedir_helper factorio
USER factorio
RUN mkdir --parents ${HOME}/.config
RUN echo 'eval "$(starship init zsh)"' >> ${HOME}/.zshrc
RUN starship preset gruvbox-rainbow --output ${HOME}/.config/starship.toml

ENTRYPOINT [ "/bin/zsh" ]
