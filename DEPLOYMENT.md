# 🚀 Guide de Déploiement

Ce guide vous aidera à déployer votre système de prédiction crypto sur différentes plateformes.

## 📋 Table des matières

- [Railway](#railway)
- [Render](#render)
- [Heroku](#heroku)
- [VPS (DigitalOcean, AWS, etc.)](#vps)
- [Configuration requise](#configuration-requise)

## Railway

Railway est parfait pour les projets Node.js avec Python.

### Étapes:

1. **Créer un compte sur Railway**
   - Visitez: https://railway.app/
   - Connectez-vous avec GitHub

2. **Créer un nouveau projet**
   - Cliquez sur "New Project"
   - Sélectionnez "Deploy from GitHub repo"
   - Choisissez votre repository

3. **Configuration automatique**
   Railway détecte automatiquement Node.js et Python!

4. **Variables d'environnement**
   - Allez dans Settings → Variables
   - Ajoutez:
     ```
     PORT=3000
     COINGECKO_API_KEY=votre_cle_si_necessaire
     ```

5. **Commandes de build**
   Railway devrait détecter automatiquement, mais vous pouvez forcer:
   - Build Command: `npm install && pip install -r requirements.txt`
   - Start Command: `node index.js`

6. **Déployer**
   - Railway déploie automatiquement à chaque push GitHub
   - Vous obtiendrez une URL comme: `your-app.railway.app`

### Buildpack Python

Si Railway ne détecte pas Python automatiquement, ajoutez un fichier `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "node index.js"
```

### Collecte de données initiale

Après le premier déploiement, appelez:
```bash
curl -X POST https://your-app.railway.app/collect_data
```

---

## Render

Render supporte également les applications multi-runtime.

### Étapes:

1. **Créer un compte Render**
   - Visitez: https://render.com/
   - Connectez-vous avec GitHub

2. **Nouveau Web Service**
   - Dashboard → New → Web Service
   - Connectez votre repository GitHub

3. **Configuration**
   - Name: `crypto-prediction-api`
   - Environment: `Node`
   - Build Command:
     ```bash
     npm install && pip3 install -r requirements.txt
     ```
   - Start Command: `node index.js`

4. **Variables d'environnement**
   Ajoutez dans Environment:
   ```
   PORT=10000
   PYTHON_VERSION=3.11
   ```

5. **Plan**
   - Choisissez "Free" pour commencer
   - Note: Les services gratuits s'arrêtent après inactivité

6. **Déployer**
   - Render déploie automatiquement
   - URL: `https://your-app.onrender.com`

### Script de build personnalisé

Créez `render-build.sh`:

```bash
#!/bin/bash
npm install
pip3 install -r requirements.txt
python3 collect_data.py
```

Puis dans Render:
- Build Command: `./render-build.sh`
- Start Command: `node index.js`

---

## Heroku

Heroku est une option classique mais nécessite plus de configuration.

### Étapes:

1. **Créer un compte Heroku**
   - Visitez: https://www.heroku.com/
   - Installez Heroku CLI

2. **Login Heroku CLI**
   ```bash
   heroku login
   ```

3. **Créer l'application**
   ```bash
   heroku create crypto-prediction-api
   ```

4. **Configurer les buildpacks**
   Heroku nécessite des buildpacks pour Node.js ET Python:
   ```bash
   heroku buildpacks:add --index 1 heroku/python
   heroku buildpacks:add --index 2 heroku/nodejs
   ```

5. **Variables d'environnement**
   ```bash
   heroku config:set COINGECKO_API_KEY=votre_cle
   ```

6. **Créer Procfile**
   Créez un fichier `Procfile` à la racine:
   ```
   web: node index.js
   ```

7. **Créer runtime.txt**
   Pour spécifier la version Python:
   ```
   python-3.11.0
   ```

8. **Déployer**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

9. **Ouvrir l'app**
   ```bash
   heroku open
   ```

10. **Collecte initiale de données**
    ```bash
    heroku run python3 collect_data.py
    ```

### Logs Heroku

Pour voir les logs:
```bash
heroku logs --tail
```

---

## VPS (DigitalOcean, AWS, Linode, etc.)

Pour un contrôle total avec un serveur VPS.

### Prérequis:
- Un VPS avec Ubuntu 22.04 LTS
- Accès SSH
- Nom de domaine (optionnel)

### Installation:

1. **Connexion SSH**
   ```bash
   ssh root@your-server-ip
   ```

2. **Installer Node.js**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. **Installer Python**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv
   ```

4. **Créer un utilisateur**
   ```bash
   adduser cryptoapp
   usermod -aG sudo cryptoapp
   su - cryptoapp
   ```

5. **Cloner le projet**
   ```bash
   git clone https://github.com/votre-repo/crypto-prediction-ai.git
   cd crypto-prediction-ai
   ```

6. **Installer les dépendances**
   ```bash
   npm install
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

7. **Collecter les données**
   ```bash
   python3 collect_data.py
   ```

8. **Installer PM2** (gestionnaire de processus)
   ```bash
   sudo npm install -g pm2
   ```

9. **Démarrer l'application**
   ```bash
   pm2 start index.js --name crypto-api
   pm2 save
   pm2 startup
   ```

10. **Configurer Nginx** (reverse proxy)
    ```bash
    sudo apt-get install -y nginx
    ```

    Créez `/etc/nginx/sites-available/crypto-api`:
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://localhost:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
    ```

    Activez le site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/crypto-api /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. **SSL avec Let's Encrypt** (optionnel)
    ```bash
    sudo apt-get install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d your-domain.com
    ```

12. **Firewall**
    ```bash
    sudo ufw allow 'Nginx Full'
    sudo ufw allow OpenSSH
    sudo ufw enable
    ```

### Maintenance VPS:

**Voir les logs:**
```bash
pm2 logs crypto-api
```

**Redémarrer l'app:**
```bash
pm2 restart crypto-api
```

**Mettre à jour l'app:**
```bash
cd crypto-prediction-ai
git pull
npm install
pip install -r requirements.txt
pm2 restart crypto-api
```

**Collecte automatique de données** (cron):
```bash
crontab -e
```

Ajoutez:
```
0 0 * * * cd /home/cryptoapp/crypto-prediction-ai && /usr/bin/python3 collect_data.py
```

---

## Configuration requise

### Variables d'environnement

Pour tous les déploiements, assurez-vous de configurer:

```env
# Port (sera défini automatiquement sur certaines plateformes)
PORT=3000

# CoinGecko API (optionnel pour le plan gratuit)
COINGECKO_API_KEY=

# Configuration du modèle
COIN_ID=bitcoin
VS_CURRENCY=usd
DATA_DAYS=30
```

### Ressources minimales

- **RAM**: 512 MB minimum (1 GB recommandé)
- **CPU**: 1 vCPU
- **Stockage**: 1 GB
- **Bande passante**: 100 GB/mois

### Versions logicielles

- Node.js: v16+ 
- Python: 3.7+
- npm: v8+
- pip: v20+

---

## 🔄 Automatisation de la collecte de données

Pour que votre système reste à jour, automatisez la collecte:

### Railway / Render / Heroku

Utilisez un service de cron externe comme:
- **Cron-job.org**: https://cron-job.org/
- **EasyCron**: https://www.easycron.com/

Configurez un appel POST toutes les heures:
```
URL: https://your-app.com/collect_data
Méthode: POST
Fréquence: Toutes les heures
```

### VPS

Utilisez crontab (voir section VPS ci-dessus).

---

## 🛡️ Sécurité

1. **Ne commitez JAMAIS** vos clés API
2. Utilisez toujours des variables d'environnement
3. Activez HTTPS en production
4. Limitez les appels API (rate limiting)
5. Surveillez les logs pour détecter les abus

---

## 📊 Monitoring

### Services recommandés:
- **UptimeRobot**: Surveillance de disponibilité
- **Sentry**: Tracking des erreurs
- **LogDNA**: Gestion des logs
- **Datadog**: Monitoring complet (payant)

---

## 💡 Conseils de déploiement

1. **Testez en local** avant de déployer
2. **Utilisez Git** pour le versioning
3. **Configurez les logs** pour faciliter le debugging
4. **Backupez** les données régulièrement
5. **Documentez** vos configurations
6. **Utilisez des secrets** pour les informations sensibles
7. **Testez les webhooks** après le déploiement

---

## 🆘 Dépannage

### Le serveur ne démarre pas
- Vérifiez les logs
- Assurez-vous que le PORT est correct
- Vérifiez que toutes les dépendances sont installées

### Erreur Python
- Vérifiez que Python 3.7+ est installé
- Assurez-vous que `market_data.csv` existe
- Vérifiez les permissions de fichiers

### Erreur API CoinGecko
- Vérifiez la limite de rate (30 appels/min)
- Utilisez une clé API si nécessaire
- Ajoutez des délais entre les appels

---

**Bonne chance avec votre déploiement! 🚀**
