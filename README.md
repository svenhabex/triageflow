# TriageFlow

<a alt="Nx logo" href="https://nx.dev" target="_blank" rel="noreferrer"><img src="https://raw.githubusercontent.com/nrwl/nx/master/images/nx-logo.png" width="45"></a>

TriageFlow is an agentic workflow system for patient triage and routing, built with Angular (frontend) and Python/FastAPI (backend) in an Nx monorepo.

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.9 or higher) - [Download here](https://python.org/)
- **uv** (Python package manager) - [Install here](https://docs.astral.sh/uv/getting-started/installation/)
- **Google Gemini API Key** - [Get one here](https://makersuite.google.com/app/apikey)

### Environment Setup

1. **Clone the repository**

   ```sh
   git clone <repository-url>
   cd triageflow
   ```

2. **Install dependencies**

   ```sh
   # Install Node.js dependencies
   npm install

   # Install Python dependencies for the backend
   npx nx install backend
   ```

3. **Create environment file**

   Create a `.env` file in the root directory and add your Gemini API key:

   ```sh
   # Create .env file
   touch .env
   ```

   Add the following content to your `.env` file:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   > **Important**: Replace `your_gemini_api_key_here` with your actual Google Gemini API key.

### Running the Applications

#### Start the Backend (Python/FastAPI)

```sh
npx nx run-dev backend
```

This will start the backend server at `http://localhost:8000`

#### Start the Frontend (Angular)

```sh
npx nx serve triageflow
```

This will start the frontend development server at `http://localhost:4200`
