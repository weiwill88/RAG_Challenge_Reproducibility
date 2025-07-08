# RAG 复现操作日记

本文件详细记录了复现RAG优胜方案过程中的每一步操作、决策依据、命令以及遇到的问题，作为可执行的操作手册和事后回顾的详实材料。

---

## Part 1: 本地环境准备

### 1. 本地环境初始化
在项目根目录 `RAG-Challenge-2/` 下执行了以下命令来创建和配置本地Python虚拟环境：
```powershell
# 切换到项目目录
cd RAG-Challenge-2

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 安装项目依赖
pip install -e . -r requirements.txt
```

### 2. 数据准备与清理
为了确保从零开始完整复现，我手动删除了 `data/test_set/` 目录下的 `databases` 和 `debug_data` 两个子文件夹。
- **理由**: 这两个文件夹包含作者预处理好的中间结果。删除它们可以保证复现的每一步流水线都使用自己生成的数据，从而能准确验证每个环节的效果。

### 3. PDF解析首次尝试 (本地)
#### 命令执行
```powershell
# 1. 切换到测试数据目录
cd data\test_set

# 2. 从项目根目录执行解析命令
python ..\..\main.py parse-pdfs
```
- **结果**: 终端日志显示 `UserWarning: 'pin_memory' argument is set as true but no accelerator is found`。
- **分析**: 这表明程序（特别是`Docling`的底层依赖`PyTorch`）需要GPU加速器但未在本地找到，导致执行失败。
- **决策**: 租用云端GPU资源以继续复现。

---

## Part 2: 云端环境配置与PDF解析

### 4. 云端GPU资源配置
#### 资源选择
- **平台**: Glows.ai
- **资源类型**: `Inference GPU`
- **GPU型号**: `NVIDIA GeForce RTX 4090`
- **配置**: 10 vCPUs, 50 GB RAM
- **价格**: 0.490 Credit/h

#### 选择理由
- **`Inference GPU` vs `Training GPU`**: 当前任务是PDF解析，属于模型推理，而非模型训练，因此`Inference GPU`是功能匹配且性价比最高的选项。
- **配置选择**: 对于处理5个PDF的小型测试集，50GB的系统内存已完全足够，选择更经济的配置可以节约成本。

### 5. 云主机镜像选择
#### 镜像选择
- **镜像ID**: `img-neqn9di2`
- **镜像名称**: `CUDA12.4 Base`
- **核心配置**: Ubuntu 20.04, CUDA 12.4, Python 3.11

#### 选择理由
1.  **纯净环境**: "Base"镜像只包含基础的CUDA和Python环境，避免了不必要的软件冲突。
2.  **版本兼容**: CUDA 12.4与Python 3.11的组合能很好地兼容`torch==2.0.0`及其他项目依赖。
3.  **安装灵活**: 我们可以自行安装`torch==2.0.0`的精确GPU版本，保证了复现的准确性，避免了因镜像预装不同版本PyTorch而可能引发的依赖问题。

### 6. 远程连接与环境设置

**a. 首次连接尝试 (失败)**
- **操作**: 在 VS Code 中选择 `Connect to Host...`，并直接输入完整SSH命令 `ssh -p 25972 root@tw-05.access.glows.ai`。
- **结果**: 连接失败，VS Code 弹出 "Could not establish connection... Connecting with SSH timed out" 错误。
- **问题分析**:
  - 查看 VS Code 的 `Remote-SSH` 输出日志发现，它将整个 `ssh -p ...` 命令错误地解析为主机名，导致连接命令构建错误，最终表现为连接超时。
  - 关键错误日志: `Running script with connection command: "C:\...\ssh.exe" -T -D ... "ssh -p 25972 root@tw-05.access.glows.ai" bash`
  - **结论**: 这不是网络问题，而是 VS Code (Cursor) 的 Remote-SSH 扩展对复杂 SSH 命令字符串的解析问题。

**b. 解决方案：使用SSH配置文件 (成功)**
- **原理**: 为复杂的连接参数创建一个简单的别名（Host），让 VS Code 可以正确、稳定地识别和连接。
- **操作步骤**:
  1.  在 VS Code 命令面板 (`Ctrl+Shift+P`) 中，运行 `Remote-SSH: Open SSH Configuration File...`。
  2.  选择默认路径 `C:\Users\YOUR_USERNAME\.ssh\config` 并打开文件。
  3.  在文件末尾添加以下配置块：
      ```
      Host glows-4090
          HostName tw-05.access.glows.ai
          User root
          Port 25972
      ```
  4.  保存并关闭 `config` 文件。
  5.  在 VS Code 中再次打开远程菜单，选择 `Connect to Host...`。
  6.  此时列表中会出现新的主机别名 `glows-4090`。点击该别名。
  7.  当提示选择远程操作系统时，选择 `Linux`。
  8.  输入密码后，成功连接。

**c. 在VS Code中打开远程项目文件夹**
- **背景**: 成功SSH连接后，VS Code的编辑器界面虽然已连接到远程主机，但文件浏览器是空的（显示 "NO FOLDER OPENED"）。
- **操作**:
  1. 点击界面左侧文件浏览器区域中的蓝色 **`Open Folder`** 按钮。
  2. 在弹出的路径输入框中，填入在服务器上克隆的项目路径：`/root/RAG-Challenge-2`。
  3. 点击“确定”或按回车。
- **结果**: VS Code 窗口刷新，左侧文件浏览器成功加载并显示出 `RAG-Challenge-2` 项目的完整目录结构。

**d. 系统更新与Git安装（规划）**
*您将在这里根据我的指导，填入实际的操作命令和结果*
```bash
# 更新apt包列表
apt update

# 安装git
apt install git -y
```

**e. 克隆项目仓库（规划）**
```bash
# 克隆代码
git clone https://github.com/IlyaRice/RAG-Challenge-2.git

# 进入项目目录
cd RAG-Challenge-2
```

**f. 配置Python环境（规划）**
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 关键：安装适配CUDA的PyTorch (项目要求torch==2.0.0)
# PyTorch官方推荐的CUDA 12.1兼容版本命令如下
pip3 install torch==2.0.0 torchvision==0.15.1 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
pip install -e . -r requirements.txt
```

### 7. 执行PDF解析（规划）
**a. 准备API密钥**
```bash
# 在云端服务器上，创建.env文件并填入您的API密钥
# 警告：请勿直接在命令行中暴露密钥
nano .env
```
`.env`文件内容示例:
```
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="..."
```

**b. 运行解析命令**
```bash
# 进入测试数据目录
cd data/test_set

# 执行PDF解析
# 我们从项目根目录执行，以保持路径一致性
python ../../main.py parse-pdfs
```
- **预期结果**: 命令成功执行，利用RTX 4090的计算能力完成PDF文件的解析，不再出现`pin_memory`警告。解析后的文件将出现在`debug_data`目录中。

---

## Part 3: 保存工作与同步 (Git)

这部分详细说明了在云端完成一天的工作后，如何将所有代码和文档的变更安全地推送到你自己的GitHub仓库，并在之后更新到你的本地电脑。

### 8. 将云端项目连接到你的GitHub仓库
**背景**: 当前云端上的项目是从原作者的仓库克隆的 (`git clone ...IlyaRice/RAG-Challenge-2.git`)。我们需要将它的远程地址（`origin`）指向你新建的空白仓库。

**操作 (在云端服务器终端执行):**

**a. 检查当前的远程地址**
```bash
# 这会显示当前项目指向的远程仓库地址，应该是原作者的
git remote -v
```

**b. 更改远程仓库地址**
```bash
# 将 'origin' 的URL更改为你自己的仓库地址
git remote set-url origin https://github.com/weiwill88/RAG_Challenge_Reproducibility.git
```

**c. 再次检查以确认更改**
```bash
# 现在应该显示你自己的仓库地址了
git remote -v
```

### 9. 推送变更到你的GitHub
**背景**: 当你在云端完成了修改（比如编辑了代码，或者上传了新的文档），就可以将这些变更作为一个“版本”提交并推送到GitHub。

**操作 (在云端服务器终端执行):**

**a. 添加所有变更到暂存区**
```bash
# '.' 代表当前目录下的所有变更
git add .
```

**b. 配置Git身份 (首次提交时需要)**
> **背景**: `git commit` 命令需要知道是谁进行的提交。首次在新的服务器环境（或任何未配置过的机器）上提交时，你需要设置你的用户名和邮箱。否则，你会遇到 `Please tell me who you are.` 的错误。这个设置只需要在每个环境中进行一次。

```bash
# 将下方命令中的邮箱和用户名替换为你自己的信息
git config user.email "weiwll666@gmail.com"
git config user.name "weiwill88"
```

**c. 提交变更**
```bash
# -m 后面是本次提交的说明，描述你做了什么
git commit -m "docs: Add operational diary and configure SSH"
```

**c. 推送到GitHub**
```bash
# -u 参数会将本地的main分支与远程的main分支关联起来，初次推送时使用
git push -u origin main
```
- **预期结果**: 你的所有代码和文档变更都会被上传到你的 GitHub 仓库 `weiwill88/RAG_Challenge_Reproducibility` 中。

### 10. 从你的GitHub同步到本地电脑
**背景**: 当你结束了云端会话，关闭了GPU实例后，你的本地电脑上的代码还是旧的。你需要从你自己的GitHub仓库拉取最新的版本。

**操作 (在你的本地电脑终端执行):**

**a. 进入本地的项目目录**
```powershell
cd path\to\your\local\RAG-Challenge-2
```

**b. 同样，更改本地仓库的远程地址**
```powershell
git remote set-url origin https://github.com/weiwill88/RAG_Challenge_Reproducibility.git
```

**c. 拉取最新更改**
```powershell
git pull origin main
```
- **预期结果**: 你在云端所做的所有工作，包括新建的文档、修改的代码，都会被完整地同步到你的本地电脑上，保持版本一致。 