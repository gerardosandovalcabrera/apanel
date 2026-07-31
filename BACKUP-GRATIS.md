# 🆓 FREE Backup Options for Hermes

Detailed comparison of free options for external backup of your Hermes installation.

## 🏆 **Top 5 Free Options - Comparison**

| Service | Free Space | Difficulty | Speed | Reliability | Recommended |
|---------|------------|------------|-------|-------------|-------------|
| **Google Drive** | 15 GB | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥇 **RECOMMENDED** |
| **GitHub** | 1 GB | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥈 VERY GOOD |
| **AWS S3 Free Tier** | 5 GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥉 GOOD (12 months) |
| **Google Cloud Storage** | 5 GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 🥉 GOOD (always) |
| **Dropbox** | 2 GB | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ Little space |

---

## 🥇 **OPTION 1: Google Drive - 15 GB FREE (RECOMMENDED)**

### ✅ **Advantages:**
- **15 GB free** - More space than most
- **Very easy to configure** - Just need a Google account
- **Access from anywhere** - Web, mobile, desktop
- **Automatic versioning** - Google keeps previous versions
- **Bidirectional sync** - You can edit files directly

### ⚙️ **Setup (5 minutes):**

#### **Step 1: Install rclone**
```bash
curl https://rclone.org/install.sh | sudo bash
```

#### **Step 2: Configure Google Drive**
```bash
# Run the automatic script
~/hermes-backup/backup-gdrive.sh
```

The script will guide you to:
1. Configure rclone with Google Drive
2. Select important files (not large databases)
3. Create automatic backups

#### **Step 3: First backup**
```bash
~/hermes-backup/backup-gdrive.sh
```

### 📊 **What gets backed up to Google Drive:**
- ✅ `config.yaml` - Complete configuration
- ✅ Skills directory - Your custom skills
- ✅ Plugins directory - Installed plugins
- ✅ Cron jobs configuration
- ✅ Documentation and notes
- ❌ Large databases (use local backup)

### 🔄 **Schedule Automatic Backups:**

```bash
# Add to crontab
crontab -e

# Backup every day at 2 AM
0 2 * * * ~/hermes-backup/backup-gdrive.sh
```

### 💾 **Restore from Google Drive:**

```bash
# List backups
rclone ls gdrive:hermes-backup/

# Restore specific file
rclone copy gdrive:hermes-backup/config.yaml ~/.hermes/config.yaml
```

---

## 🥈 **OPTION 2: GitHub - 1 GB FREE (VERY GOOD)**

### ✅ **Advantages:**
- **Version control built-in** - Git tracks all changes
- **Collaboration** - Easy to share with team
- **Issue tracking** - For documentation
- **Free private repos** - Your backups stay private
- **Reliable** - Used by millions of developers

### ⚙️ **Setup (10 minutes):**

#### **Step 1: Create GitHub Repository**

1. Go to https://github.com/new
2. Create private repository: `hermes-backup`
3. Generate personal access token:
   - Settings → Developer settings → Personal access tokens
   - Generate token with `repo` scope
   - **Save the token** (you won't see it again)

#### **Step 2: Configure backup script**

```bash
# Set your GitHub token
export GITHUB_TOKEN='your-token-here'

# Run first backup
~/hermes-backup/backup-github-safe.sh
```

### 📊 **What gets backed up to GitHub:**
- ✅ All configuration files
- ✅ Skills and plugins
- ✅ Cron job configs
- ✅ Documentation
- ✅ **SECURE**: Excludes .env, auth.json, secrets

### 🔒 **Security Features:**

The backup script automatically excludes:
```bash
.env
.env.*
auth.json
*.key
*.pem
secrets/
credentials/
```

### 💾 **Restore from GitHub:**

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/hermes-backup.git ~/hermes-restore

# Copy files to Hermes
cp -r ~/hermes-restore/* ~/.hermes/
```

---

## 🥉 **OPTION 3: AWS S3 Free Tier - 5 GB FREE (GOOD for 12 months)**

### ✅ **Advantages:**
- **5 GB storage** free for 12 months
- **Industry standard** - Used by major companies
- **High reliability** - 99.999999999% durability
- **Fast access** - Global CDN
- **Versioning** - Keeps file history

### ⚠️ **Disadvantages:**
- **Limited to 12 months** - Then you must pay
- **More complex setup** - Requires AWS account
- **Learning curve** - Need to understand S3

### ⚙️ **Setup (20 minutes):**

#### **Step 1: Create AWS Account**

1. Go to https://aws.amazon.com/free/
2. Sign up (credit card required)
3. Verify identity

#### **Step 2: Create S3 Bucket**

```bash
# Install AWS CLI
pip3 install awscli

# Configure credentials
aws configure

# Create bucket
aws s3 mb s3://hermes-backup-bucket
```

#### **Step 3: Backup command**

```bash
# Backup entire Hermes directory
aws s3 sync ~/.hermes s3://hermes-backup-bucket/hermes --exclude "*.db"
```

### 📊 **Free Tier Limits:**
- **Storage:** 5 GB/month
- **Requests:** 20,000 GET/month
- **Data transfer:** 15 GB/month

---

## 🥉 **OPTION 4: Google Cloud Storage - 5 GB FREE (GOOD always)**

### ✅ **Advantages:**
- **5 GB free** - Always free, not limited to 12 months
- **Fast** - Google's network
- **Reliable** - 99.999999999% durability
- **Easy to use** - Web console + CLI
- **Integrates with other Google services**

### ⚙️ **Setup (15 minutes):**

#### **Step 1: Create GCP Project**

1. Go to https://console.cloud.google.com/
2. Create new project: `hermes-backup`
3. Enable Cloud Storage API

#### **Step 2: Create bucket**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Create bucket
gsutil mb -l us gs://hermes-backup
```

#### **Step 3: Backup command**

```bash
# Backup to GCS
gsutil -m rsync -r ~/.hermes gs://hermes-backup/hermes
```

---

## 📋 **Comparison Summary**

| Feature | Google Drive | GitHub | AWS S3 | GCS |
|---------|--------------|--------|--------|-----|
| **Free Space** | 15 GB | 1 GB | 5 GB (12 mo) | 5 GB (always) |
| **Setup Time** | 5 min | 10 min | 20 min | 15 min |
| **Version Control** | ✅ Auto | ✅ Git | ✅ Optional | ✅ Optional |
| **Collaboration** | ✅ | ✅ | ✅ | ✅ |
| **Learning Curve** | Easy | Easy | Medium | Medium |
| **Best For** | Personal use | Teams | Enterprise | Professional |

---

## 🎯 **Recommendation: Use BOTH Google Drive + GitHub**

### **Strategy:**
1. **Google Drive** - Daily automated backups of config and skills
2. **GitHub** - Version control of important configs and documentation

### **Setup:**

```bash
# Daily backup to Google Drive (2 AM)
0 2 * * * ~/hermes-backup/backup-gdrive.sh

# Weekly push to GitHub (Sunday at 3 AM)
0 3 * * 0 cd ~/hermes && git add . && git commit -m "Weekly backup" && git push
```

---

## 💡 **Best Practices**

### **1. Automate Everything**
```bash
# Add to crontab
crontab -e

# Daily automated backup
0 2 * * * ~/hermes-backup/backup-gdrive.sh
```

### **2. Test Your Backups**
```bash
# Monthly test: restore to a temp directory
mkdir /tmp/hermes-test
rclone copy gdrive:hermes-backup /tmp/hermes-test
```

### **3. Monitor Storage**
```bash
# Check Google Drive usage
rclone about gdrive:

# Check GitHub repo size
# Visit: https://github.com/YOUR_USERNAME/hermes-backup/settings
```

### **4. Keep Multiple Copies**
- **Local backup** - Fast restore
- **Google Drive** - Offsite, versioned
- **GitHub** - Version control, collaboration

---

## 🚨 **What NOT to Backup**

❌ **Don't backup:**
- Large databases (> 100 MB)
- Temporary files
- Cache directories
- Virtual environments
- Node modules

✅ **DO backup:**
- Configuration files
- Custom skills
- Plugins
- Documentation
- Cron jobs
- Important scripts

---

## 📞 **Support**

If you need help:
- **Google Drive**: https://support.google.com/drive
- **GitHub**: https://docs.github.com
- **AWS S3**: https://docs.aws.amazon.com/s3/
- **GCS**: https://cloud.google.com/storage/docs

---

**Last Updated:** 2025-07-31
**Recommended Option:** Google Drive (15 GB free)
**Alternative:** GitHub (for version control)
