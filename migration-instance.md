# 🚀 How to Set Up and Use the Migration Project on an AWS Ubuntu Instance

This guide walks you through creating an AWS EC2 instance, preparing the environment, cloning the [Migration GitHub repository](https://github.com/AdarBahar/Migration), and running its Python tools for Redis migration, comparison, and testing.

---

## 1. 🛠️ Create an AWS EC2 Instance

1. Go to the **AWS EC2 Console**.
2. Click **Launch Instance**.
3. Configure as follows:

   * **AMI**: Ubuntu Linux (latest LTS preferred)
   * **Instance type**: `t3.micro` or larger
   * **VPC & Subnet**: Use or create a compatible VPC and subnet
   * **Security Group**: Assign a group that allows SSH from your IP
   * **Key pair (login)**: Create or select an existing `.pem` file
4. Launch the instance and copy its **public IP**.

📌 **Tip**: Download the `.pem` file and store it securely. You'll use it to connect via SSH.

---

## 2. 🔐 Configure Security Group for SSH Access

To allow your local machine to connect via SSH:

1. Navigate to **EC2 > Security Groups**.
2. Select your group (e.g., `sg-xxxxx`).
3. Click **Inbound Rules > Edit Inbound Rules**.
4. Add a rule:

   * **Type**: SSH
   * **Port**: 22
   * **Source**: `Your IP address` (in CIDR format, e.g. `203.0.113.42/32`)
5. Click **Save rules**.

📌 Make sure the **Security Group** and the **Subnet** belong to the **same VPC** to avoid launch errors.

---

## 3. 💻 Connect to Your Instance via SSH

From your terminal (macOS/Linux/WSL):

```bash
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ubuntu@<public-ip>
```

✅ Replace `/path/to/your-key.pem` and `<public-ip>` accordingly.

---

## 4. ⚙️ Set Up the Python Environment

### 🔎 Check Python

```bash
python3 --version
```

* If Python is present (e.g., `Python 3.10.12`), proceed.
* If not, install it:

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

### 🔄 Update Package Lists

Ensure your package manager is up-to-date:

```bash
sudo apt update
sudo apt upgrade -y
sudo add-apt-repository universe
sudo apt update
```

### 🐍 Install Python Virtual Environment

```bash
sudo apt install python3-venv -y
```

### 🧬 Install Git

```bash
sudo apt install git -y
```

---

## 5. 📥 Clone and Set Up the Migration Repository

### 📦 Clone the repo

```bash
git clone https://github.com/AdarBahar/Migration.git
```

### 🏗️ Create and Activate a Virtual Environment

```bash
cd Migration
python3 -m venv venv
source venv/bin/activate
```

### 📚 Install Requirements

```bash
pip install -r requirements.txt
```

---

## 6. 🔧 Manage Environments with `manage_env.py`

Run the environment manager tool:

```bash
python manage_env.py
```

This tool helps you define Redis source and destination configurations stored in a `.env` file.

📝 **Important Notes**:

* **AWS Redis OSS**:

  * Usually **uses TLS**
  * **No password**
* **Redis Cloud**:

  * **Does not use TLS**
  * **Requires password**

You'll be prompted to enter connection strings and names for each environment.

---

## 7. 🚀 Available Scripts

Here’s what each script does in the `Migration` project:

| Script            | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| `DB_compare.py`   | Live compare keys/tables between source and destination Redis            |
| `ReadWriteOps.py` | Run multi-threaded read/write tests; logs latency per operation          |
| `flushDBData.py`  | Interactively flush one or both Redis databases                          |
| `manage_env.py`   | CLI tool to manage Redis connection strings and friendly names in `.env` |
| `datafaker.py`    | Generate fake data for Redis testing                                     |

---

## ✅ Final Notes

* Run `source venv/bin/activate` again in each new SSH session before using the scripts.
* Make sure your Redis environments are accessible from your EC2 instance (correct IP allowlists, no firewalls blocking ports, etc.).
* Keep your `.pem` file secure and never commit it to source control.

---

## 📦 Launch with CloudFormation (Recommended)

🚀 **Skip manual setup entirely!** Launch the entire environment via AWS CloudFormation with our pre-configured template:

👉 [Click here to launch the stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create/review?templateURL=https://adar-testing.s3.eu-north-1.amazonaws.com/migration-instance.yaml)

### ✨ What the CloudFormation Template Automatically Does:
- ✅ **Creates Ubuntu EC2 instance** (t3.micro by default, free tier eligible)
- ✅ **Uses default AMI**: `ami-042b4708b1d05f512` (Ubuntu 22.04 LTS in us-east-1)
- ✅ **Default stack name**: `Redis-Migration-Tool`
- ✅ **Updates system packages** (`apt update && upgrade`)
- ✅ **Installs all dependencies**: Python 3, pip, venv, Git, curl, wget, unzip, AWS CLI
- ✅ **Installs CloudFormation helpers** for proper signaling
- ✅ **Clones this repository** from GitHub
- ✅ **Creates virtual environment** and installs requirements
- ✅ **Sets up IAM role** with ElastiCache, EC2, and VPC permissions
- ✅ **Detects region automatically** (eu-north-1, us-east-1, etc.) with IMDSv2 support
- ✅ **Creates region detection script** for ElastiCache provisioning
- ✅ **Sets up security group** for SSH access from your IP only
- ✅ **Creates convenience scripts** for easy environment activation
- ✅ **Creates setup verification script** to test all components
- ✅ **Sets proper file ownership** for ubuntu user
- ✅ **Ensures public IP assignment** (requires public subnet with auto-assign enabled)
- ✅ **Waits for completion**: Shows CREATE_COMPLETE only after all software is installed (20 min timeout)

### CloudFormation Parameters:

| Parameter                  | Where to Find It                                                             | Default Value              | Notes                                    |
| -------------------------- | ---------------------------------------------------------------------------- | -------------------------- | ---------------------------------------- |
| **StackName**              | Automatically set                                                            | `Redis-Migration-Tool`     | Used for resource naming and tagging    |
| **KeyName**                | EC2 Console → Network & Security → Key Pairs                                 | (required)                 | Create one if you don't have any        |
| **MyIP**                   | Get your public IP at [checkip.amazonaws.com](https://checkip.amazonaws.com) | (required)                 | Add '/32' to the end (e.g., 1.2.3.4/32) |
| **VpcId**                  | VPC Console → Your VPCs                                                      | (required)                 | Use default VPC if unsure               |
| **SubnetId**               | VPC Console → Subnets (must belong to selected VPC)                          | (required)                 | ⚠️ Must be PUBLIC subnet with auto-assign IP enabled |
| **AmiId**                  | EC2 Console → AMIs → Filter by Canonical + Ubuntu                            | `ami-042b4708b1d05f512`    | Ubuntu 22.04 LTS (us-east-1 region)     |
| **DefaultSecurityGroupId** | VPC Console → Security Groups → Look for `Group Name = default` in your VPC  | (required)                 | Every VPC has a default security group  |
| **InstanceType**           | Choose instance size                                                         | `t3.micro`                 | t3.micro is free tier eligible          |

### 💡 Quick Setup Tips:

1. **First time AWS user?** Use your default VPC and any public subnet within it
2. **Don't have a Key Pair?** Create one in EC2 Console → Key Pairs → Create key pair
3. **Finding your IP:** Visit [checkip.amazonaws.com](https://checkip.amazonaws.com), copy the IP, and add `/32`
4. **Default Security Group:** In VPC Console, filter by your VPC ID and look for the group named "default"
5. **AMI varies by region:** The default AMI is for us-east-1. For other regions, search for "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04"

### 🔍 Step-by-Step Parameter Collection:

**Before launching the CloudFormation stack, gather these values:**

1. **Your Public IP**: Go to https://checkip.amazonaws.com → Copy IP → Add `/32` (e.g., `203.0.113.42/32`)

2. **VPC ID**: AWS Console → VPC → Your VPCs → Copy the VPC ID (starts with `vpc-`)

3. **Subnet ID**: AWS Console → VPC → Subnets → Filter by your VPC → Choose a public subnet → Copy Subnet ID (starts with `subnet-`)

4. **Default Security Group**: AWS Console → VPC → Security Groups → Filter by your VPC → Find group with name "default" → Copy Group ID (starts with `sg-`)

5. **Key Pair**: AWS Console → EC2 → Key Pairs → Create or select existing → Note the name (not the file path)

### ⏱️ Deployment Timing:

**Important**: The CloudFormation stack will show `CREATE_IN_PROGRESS` for 15-20 minutes while all software is being installed. The stack will only show `CREATE_COMPLETE` when everything is fully configured and ready to use.

### 🎯 After CloudFormation Deployment:

Once your stack shows `CREATE_COMPLETE` (meaning all installation is finished):

### 🔍 Verify Installation:

```bash
# SSH to your instance
ssh -i /path/to/your-key.pem ubuntu@<public-ip>

# Run the verification script
cd /home/ubuntu/Migration
./verify_setup.sh

# Should show:
# ✅ Region detected: eu-north-1 (or your region)
# ✅ Virtual environment activated
# ✅ AWS CLI available
# ✅ ElastiCache provisioner ready
```

### 🚀 Provision ElastiCache (Out-of-the-Box):

1. **Get the public IP** from the CloudFormation Outputs tab
2. **SSH to your instance**:
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@<public-ip>
   ```

3. **Activate the virtual environment** using one of these methods:

   **Method 1: Manual activation (recommended)**
   ```bash
   cd /home/ubuntu/Migration
   source venv/bin/activate
   ```

   **Method 2: Use the convenience alias**
   ```bash
   # After logout/login, you can use:
   activate-migration
   ```

   **Method 3: Get information and instructions**
   ```bash
   ./start-migration.sh
   ```

4. **Provision ElastiCache (Out-of-the-Box)**:
   ```bash
   # Provision ElastiCache - now works automatically!
   python provision_elasticache.py

   # The script will:
   # ✅ Auto-detect your region (eu-north-1, us-east-1, etc.)
   # ✅ Auto-detect your VPC and subnets
   # ✅ Create security groups automatically
   # ✅ Provision ElastiCache cluster
   # ✅ Update your .env file with connection details
   ```

5. **Complete Migration Workflow**:
   ```bash
   # Configure environment variables (if needed)
   python manage_env.py

   # Generate test data
   python DataFaker.py

   # Compare databases
   python DB_compare.py

   # Run performance tests
   python ReadWriteOps.py

   # Clean up when done
   python cleanup_elasticache.py
   ```

### 🎯 Key Features - Out-of-the-Box Ready:

- ✅ **Automatic region detection** - Works in any AWS region
- ✅ **IMDSv2 support** - Compatible with modern EC2 security settings
- ✅ **Complete IAM permissions** - ElastiCache, EC2, VPC access included
- ✅ **VPC auto-discovery** - Finds and uses your existing VPC
- ✅ **Error handling** - Comprehensive fallbacks and manual options
- ✅ **Verification tools** - Built-in setup verification script

### 🔧 Virtual Environment Notes:

- **The venv is pre-installed** but needs to be activated in each SSH session
- **All dependencies are already installed** (redis, python-dotenv, faker, boto3)
- **The convenience script** `./start-migration.sh` provides activation instructions
- **An alias** `activate-migration` is available after logout/login
- **Verification script** `./verify_setup.sh` tests all components

### 🚀 Ready to Use:

Your CloudFormation deployment creates a **complete, production-ready** Redis migration environment that works immediately after deployment completes. No manual configuration required!

Happy migrating! 🧠🔁📦
