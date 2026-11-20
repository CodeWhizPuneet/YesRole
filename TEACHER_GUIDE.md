# Show YesRole to your teacher

Use **GitHub for the source code** and a **free Cloudflare Quick Tunnel for a live demo**. Share two links. The GitHub link shows the code and documentation. The HTTPS demo link opens the working app.

## 1. Run locally in VS Code

1. Open `D:\workspace\PROJECT\YesRole AI` in VS Code.
2. Press **Ctrl+Shift+P**, choose **Tasks: Run Task**, then choose **YesRole: Start local app**.
3. Open [YesRole](http://127.0.0.1:5173). Choose **Try Demo → Machine Learning Engineer Intern → Analyze Resume Match**.
4. Stop the task when done. For a fresh checkout, use the [Windows setup instructions](README.md#run-on-windows-with-powershell).

## 2. Publish the source on GitHub

1. Sign in to GitHub. Create a repository named **yesrole**. Choose **Public** for a portfolio link, and leave the README, .gitignore and license checkboxes unchecked.
2. Open the VS Code PowerShell terminal and run `git --version`. If it isn't recognized, install Git for Windows and reopen VS Code. [Git for Windows](https://git-scm.com/install/windows)
3. Run these commands from the project folder. Replace YOUR-USERNAME with your GitHub username. Stop to review `git status --short` before committing.

```powershell
git init -b main
git add -- .gitignore .dockerignore .env.example .vscode Dockerfile Run-YesRole.ps1 README.md DEMO_GUIDE.md DEPLOY.md TEACHER_GUIDE.md frontend backend docs stitch-design
git status --short
git commit -m "Build YesRole resume matching platform"
git remote add origin https://github.com/YOUR-USERNAME/yesrole.git
git push -u origin main
```

Source, screenshots with fictional data, and the fictional demo fixtures belong in the repository. Keep secrets, personal resumes, local databases and model weights out. If Git asks you to sign in, complete the GitHub browser prompt. If it asks for your commit identity, set your name and email with `git config user.name "Your Name"` and `git config user.email "you@example.com"`, then retry the commit. [GitHub guide to pushing existing code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)

## 3. Create a free live demo link from your PC

A Cloudflare Quick Tunnel gives you a temporary HTTPS address without a Cloudflare account or domain. Your PC must stay awake and online, and both processes must keep running. Restarting the tunnel gives you a new URL. [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

1. Install the Windows cloudflared MSI. Open a new terminal and run `cloudflared --version`. [Cloudflare downloads](https://developers.cloudflare.com/tunnel/downloads/)
2. In **terminal 1**, run the following. Copy the HTTPS address printed by cloudflared. Leave the terminal running.

   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8080
   ```
3. In **terminal 2** at the YesRole project root, paste the command below with the exact URL from terminal 1. Wait for Uvicorn to say it is running. The launcher builds the website and serves it alongside the API behind a generated demo password.

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Run-YesRole.ps1 -TeacherUrl 'https://replace-with-your-url.trycloudflare.com'
   ```
4. Open the HTTPS link in a private browser window. Sign in as **yesrole** using the password printed in terminal 2. Run **Try Demo** to verify the entire flow. Share the link and credentials with your teacher privately.
5. Leave both terminals running through the evaluation. Stop them with Ctrl+C afterward. The teacher demo uses a separate database from your local analysis history. Everyone with the demo password shares the demo history, so use fictional samples.

If you see a gateway error, wait until terminal 2 says Uvicorn is running and check that both processes use port 8080. If the school network blocks the tunnel, run the normal local app and share your screen.

## 4. Options that run on a cloud computer

### GitHub Codespaces for a temporary cloud demo

Use your personal GitHub account's included Codespaces quota if you have enough left. The link works while the codespace and app are running. The codespace can stop after inactivity. Check compute and storage usage and leave paid usage disabled to stay within the included quota. [Codespaces included usage](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage) · [Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)

1. Open the GitHub repository and choose **Code → Codespaces → Create codespace on main**. Open the remote **Terminal**. The following commands use Bash.
2. Build the image containing the website, API and MiniLM weights.

   ```bash
   docker build -t yesrole-demo .
   ```
3. Choose a strong ASCII demo password of at least 16 characters. The prompt keeps it out of shell history.

   ```bash
   demo_host="$CODESPACE_NAME-8000.$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"
   read -rsp 'Demo password: ' YESROLE_DEMO_PASSWORD
   printf '\n'
   export YESROLE_DEMO_PASSWORD
   docker run --rm -p 127.0.0.1:8000:8000 \
     -e YESROLE_DEMO_PASSWORD \
     -e "YESROLE_ALLOWED_HOSTS=$demo_host,localhost,127.0.0.1" \
     -e "YESROLE_CORS_ORIGINS=https://$demo_host" \
     yesrole-demo
   ```
4. In the **Ports** panel, forward port **8000** and set **Port Visibility → Public**. Check that the copied hostname matches `demo_host`. Test the URL in a private window using the YesRole username **yesrole** and password. If your repository policy disallows public ports, use the Cloudflare route. Stop the codespace afterward. [GitHub port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace)

### Azure for Students for a longer-lived link

Eligible students receive **US$100 in Azure credits with no credit card at signup**. Azure Container Apps and Container Registry can consume this credit. Use the [Azure deployment instructions](DEPLOY.md) if your teacher requires Azure or needs a link that works while your PC is off. [Azure for Students terms](https://azure.microsoft.com/en-us/pricing/offers/ms-azr-0170p/)

Hugging Face lists CPU Basic at zero hourly cost, but its current documentation says creating a Docker or Gradio Space generally requires a paid plan. Static hosting can publish a frontend. YesRole's analysis also needs the running Python API. [Hugging Face Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview)

## 5. Explain the model in class

The browser sends the resume and target job description to the **FastAPI backend**. The backend runs **all-MiniLM-L6-v2**, a pretrained embedding model. It converts job requirements and resume passages to 384-number vectors. Cosine similarity retrieves likely evidence, and YesRole's verification rules decide how well it supports the requirement. A Python passage can be relevant to an ML posting and still leave its Docker requirement unevidenced. [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

The model runs wherever the backend runs. Through the Cloudflare link, it runs on your PC. In Codespaces or Azure it runs on the cloud machine, with the weights included by the Docker build. Your teacher uses a browser. The matching workflow requires no OpenAI key, Azure AI subscription, or separate generative LLM. The optional local AI ranks existing rewrite suggestions and can stay disabled.

### Show this in two minutes

1. Open the GitHub README and show the architecture.
2. Open the demo link and analyze the fictional **Machine Learning Engineer Intern** resume.
3. Expand the Python evidence and the Docker gap. Show the separate ATS Readability checks.
4. Make a truthful wording edit in Studio, reanalyze, and export a PDF or DOCX. The score can stay the same when the evidence stays the same.

See the [two-minute script and viva questions](DEMO_GUIDE.md).

