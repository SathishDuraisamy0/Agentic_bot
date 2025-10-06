# ----------------------------
# 1️⃣  Start from the official Jenkins image
# ----------------------------
FROM jenkins/jenkins:lts

# ----------------------------
# 2️⃣  Switch to root to install packages
# ----------------------------
USER root

# ----------------------------
# 3️⃣  Install required system packages and Docker Engine
# ----------------------------
RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get clean

# ----------------------------
# 4️⃣  Add Jenkins user to the Docker group
# (so Jenkins can run docker build / run / push)
# ----------------------------
RUN groupadd -f docker && \
    usermod -aG docker jenkins

# ----------------------------
# 5️⃣  Create directory for Docker runtime data
# ----------------------------
RUN mkdir -p /var/lib/docker
VOLUME /var/lib/docker

# ----------------------------
# 6️⃣  Switch back to Jenkins user
# ----------------------------
USER jenkins

# ----------------------------
# 7️⃣  Jenkins will automatically start on port 8080
# ----------------------------
