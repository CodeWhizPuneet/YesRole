# Run and deploy YesRole

## Run in VS Code on this Windows computer

1. Open `D:\workspace\PROJECT\YesRole AI` using **File → Open Folder**. Open the project root so VS Code sees the launcher, frontend, and backend.
2. In VS Code, press **Ctrl+Shift+P**, choose **Tasks: Run Task**, and select **YesRole: Start local app**. You can also run the following in a PowerShell terminal at the project root.

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Run-YesRole.ps1
   ```

3. Open [YesRole](http://127.0.0.1:5173) and select **Try Demo**. You can check the backend at [the health endpoint](http://127.0.0.1:8000/api/health). Stop the task to free both ports.

This workspace already has dependencies and the model cached. For a fresh checkout, follow [the README installation steps](README.md#run-on-windows-with-powershell). If you use the Microsoft Python extension, select `.venv\Scripts\python.exe` via **Python: Select Interpreter**. If startup fails, check `.runtime/api-error.log` and `.runtime/web-error.log`.

## Deploy an Azure demo

The Dockerfile builds the React frontend, installs the FastAPI backend and CPU PyTorch, and packages the pinned MiniLM weights. One container serves the React routes and `/api` on port **8000**. The hosted entry point requires a shared password. Use the Azure HTTPS URL for the demo.

### 1. Build the image in Azure Container Registry

Install [Azure CLI for Windows](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows), sign in, and run from the project root. Choose your Azure subscription and a region available to it. Pick a globally unique lowercase alphanumeric registry name.

```powershell
az login
$group = 'yesrole-demo-rg'
$region = 'centralindia'
$registry = '<your-unique-registry-name>'
az group create --name $group --location $region
az acr create --resource-group $group --name $registry --sku Basic --role-assignment-mode rbac
az acr build --registry $registry --image yesrole:demo-v1 --file Dockerfile .
```

ACR runs the Docker build remotely. The build context excludes local databases, resume files, the Python virtual environment, model cache, and environment files. Azure builds, registry storage, and running resources can incur charges. [Microsoft Learn ACR build guide](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-quickstart-task-cli) · [Azure Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing)

### 2. Create the Container App and configure access

1. In Azure Portal, create a **Container App** in the same resource group and region using the quickstart image. Enable its **system-assigned managed identity** and assign that identity **AcrPull** on the registry. [Microsoft Learn managed identity image pull](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity-image-pull)
2. In the Container App's **Secrets** page, add `demo-password` with a strong random ASCII password of at least 16 characters. Keep the password out of source files and terminal history. [Microsoft Learn Container Apps secrets](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
3. Enable **external HTTP ingress** with insecure connections disabled and copy the HTTPS application URL from **Overview**. The quickstart image uses port 80. Change the target port to **8000** when switching to the YesRole image. If you set custom HTTP health probes, use port **8000** and path `/healthz`. [Microsoft Learn ingress setup](https://learn.microsoft.com/en-us/azure/container-apps/ingress-how-to)
4. Create a revision using `<registry-login-server>/yesrole:demo-v1` and your managed identity for the image pull. Set the following environment variables on that revision. Start with **1 vCPU and 2 GiB** and set a maximum of **one replica** for the shared demo history. [Microsoft Learn environment variables](https://learn.microsoft.com/en-us/azure/container-apps/environment-variables)

| Variable | Value |
| --- | --- |
| `YESROLE_DEMO_PASSWORD` | Secret reference to `demo-password` |
| `YESROLE_ALLOWED_HOSTS` | The hostname from your Container Apps URL, without `https://` |
| `YESROLE_CORS_ORIGINS` | The full HTTPS origin, without a trailing slash |

### 3. Verify the deployed demo

1. Visit `https://<your-app-host>/healthz` to verify that the app is responding.
2. Visit the HTTPS app URL in a private browser window. Sign in with username `yesrole` and the demo password. Run **Try Demo → Analyze Resume Match**, open the report, and refresh the report URL.
3. Reanalyze a fictional draft in Studio and export a PDF. Stop or remove demo resources when you no longer need them and have checked which resources share the group.

Everyone with the demo password shares the same server report history. Use fictional resumes for the hosted demo. The container's SQLite history is temporary and may disappear when the replica restarts or scales to zero. A public job-seeker rollout needs per-user authentication, durable storage, and retention controls. [Microsoft Learn Container Apps storage](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts)

