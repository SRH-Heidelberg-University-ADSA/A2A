import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import base64
import io
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn
import tempfile

# Load environment variables
load_dotenv()

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_AI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

# Set up plotting style
try:
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
except:
    plt.style.use('default')

class DataExplorerAgent:
    def __init__(self, data_dir='data', output_dir='output'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def load_csv(self, csv_path):
        """Load CSV file and return DataFrame."""
        try:
            df = pd.read_csv(csv_path)
            print(f"Successfully loaded {csv_path}")
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None

    def inspect_dataset(self, df):
        """Inspect columns, data types, and basic statistics."""
        print("\n" + "="*50)
        print("DATASET OVERVIEW")
        print("="*50)

        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"\nColumns and Data Types:")
        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isnull().sum()
            print(f"  {col}: {dtype} (nulls: {null_count})")

        print(f"\nData Types Summary:")
        print(df.dtypes.value_counts())

        # Check for datetime columns
        datetime_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                    datetime_cols.append(col)
                except:
                    pass

        if datetime_cols:
            print(f"\nDatetime columns detected: {datetime_cols}")
            for col in datetime_cols:
                print(f"  {col} range: {df[col].min()} to {df[col].max()}")

        return datetime_cols

    def compute_basic_stats(self, df):
        """Compute basic statistics for numeric columns."""
        print("\n" + "="*50)
        print("BASIC STATISTICS")
        print("="*50)

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe()
            print(stats)
            return stats
        else:
            print("No numeric columns found.")
            return None

    def analyze_correlations(self, df):
        """Analyze correlations between numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            print("\n" + "="*50)
            print("CORRELATION ANALYSIS")
            print("="*50)
            print(corr_matrix)
            return corr_matrix
        return None

    def create_visualizations(self, df, prefix="dataset"):
        """Create meaningful visualizations."""
        print("\n" + "="*50)
        print("VISUALIZATIONS")
        print("="*50)

        visualizations = []

        # Histogram for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                plt.figure(figsize=(8, 6))
                sns.histplot(df[col], kde=True, bins=30)
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Frequency')
                plt.tight_layout()
                hist_path = self.output_dir / f"{prefix}_{col}_hist.png"
                plt.savefig(hist_path, dpi=150, bbox_inches='tight')
                plt.close()
                visualizations.append(str(hist_path))
            except Exception as e:
                print(f"Could not create histogram for {col}: {e}")

        # Bar plots for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].nunique() <= 20:  # Only plot if not too many categories
                try:
                    plt.figure(figsize=(10, 6))
                    value_counts = df[col].value_counts()
                    sns.barplot(x=value_counts.index, y=value_counts.values)
                    plt.title(f'Distribution of {col}')
                    plt.xlabel(col)
                    plt.ylabel('Count')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    bar_path = self.output_dir / f"{prefix}_{col}_bar.png"
                    plt.savefig(bar_path, dpi=150, bbox_inches='tight')
                    plt.close()
                    visualizations.append(str(bar_path))
                except Exception as e:
                    print(f"Could not create bar chart for {col}: {e}")

        return visualizations

    def analyze_question_with_llm(self, df, question, analysis_context):
        """Analyze question using LLM based on computed analysis."""
        print("\n" + "="*50)
        print("QUESTION ANALYSIS")
        print("="*50)
        print(f"Question: {question}")

        # Prepare context from analysis
        context_parts = []

        # Dataset info
        context_parts.append(f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns.")
        context_parts.append(f"Columns: {', '.join(df.columns.tolist())}")

        # Data types
        dtypes_info = []
        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isnull().sum()
            dtypes_info.append(f"{col} ({dtype}, {null_count} nulls)")
        context_parts.append(f"Column details: {'; '.join(dtypes_info)}")

        # Basic stats
        if 'basic_stats' in analysis_context and analysis_context['basic_stats'] is not None:
            stats_str = analysis_context['basic_stats'].to_string()
            context_parts.append(f"Basic statistics:\n{stats_str}")

        # Correlations
        if 'correlations' in analysis_context and analysis_context['correlations'] is not None:
            corr_str = analysis_context['correlations'].to_string()
            context_parts.append(f"Correlation matrix:\n{corr_str}")

        # Unique counts
        unique_counts = df.nunique()
        unique_info = [f"{col}: {count}" for col, count in unique_counts.items()]
        context_parts.append(f"Unique value counts: {'; '.join(unique_info)}")

        full_context = "\n\n".join(context_parts)

        # Use LLM to answer question
        try:
            prompt = f"""Based on the following dataset analysis, answer the user's question accurately using only the provided information.

Dataset Analysis Context:
{full_context}

Question: {question}

Instructions:
- Use only the data and statistics provided above
- Be precise and factual
- If the question cannot be answered from the available data, say so clearly
- Provide clear, concise answers
- Include specific numbers when available

Answer:"""

            response = model.generate_content(prompt)
            answer = response.text.strip()
            return answer

        except Exception as e:
            print(f"Error using LLM: {e}")
            return "Unable to generate insights due to an error."

    def run_analysis_pipeline(self, df, question=None, file_prefix="analysis"):
        """Run the full analysis pipeline on a dataframe."""
        
        # Inspect dataset
        datetime_cols = self.inspect_dataset(df)

        # Basic statistics
        basic_stats = self.compute_basic_stats(df)

        # Correlations
        correlations = self.analyze_correlations(df)

        # Visualizations
        self.create_visualizations(df, prefix=file_prefix)

        # Prepare analysis context for LLM
        analysis_context = {
            'basic_stats': basic_stats,
            'correlations': correlations
        }

        # Question analysis
        final_insight = "Analysis complete. Visualizations saved."
        if question:
            final_insight = self.analyze_question_with_llm(df, question, analysis_context)
        else:
            # Generate a general summary if no question
             final_insight = self.analyze_question_with_llm(df, "Generate a comprehensive summary of this dataset.", analysis_context)
             
        return final_insight


# --- FastAPI / JSON-RPC Helper Code ---
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DS_Agent")

app = FastAPI()
agent = DataExplorerAgent()


# ── Bearer Token Authentication ──────────────────────────────────────────────
def verify_bearer_token(authorization: str = Header(..., description="Bearer token for authentication")):
    """
    Validates the Authorization header contains a valid Bearer token.
    Token is read from DS_AGENT_BEARER_TOKEN env var.
    """
    expected_token = os.getenv("DS_AGENT_BEARER_TOKEN", "")
    if not expected_token:
        logger.warning("DS_AGENT_BEARER_TOKEN not set — all requests will be rejected!")
        raise HTTPException(status_code=500, detail="Server auth not configured")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must use Bearer scheme")

    provided_token = authorization[7:]  # Strip "Bearer " prefix
    if provided_token != expected_token:
        logger.warning("Invalid bearer token received")
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token")

    logger.info("Bearer token verified successfully")
    return provided_token


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: dict
    id: int | str

@app.get("/")
def read_root():
    return {
        "agent": "Data Analyst",
        "status": "Ready for A2A tasks",
        "auth": "Bearer token required on /jsonrpc",
        "docs": "/docs"
    }

@app.post("/jsonrpc", dependencies=[Depends(verify_bearer_token)])
async def json_rpc_endpoint(request: JSONRPCRequest):
    logger.info(f"Received RPC Request ID: {request.id} Method: {request.method}")
    
    if request.jsonrpc != "2.0":
        logger.error("Invalid JSON-RPC version")
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")

    if request.method == "analyze_dataset":
        response = await handle_analyze_dataset(request)
        logger.info(f"Completed RPC Request ID: {request.id}")
        return response
    else:
        logger.warning(f"Method not found: {request.method}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": "Method not found"},
            "id": request.id
        }

async def handle_analyze_dataset(request: JSONRPCRequest):
    try:
        logger.info(f"Starting analysis for Request ID: {request.id}")
        params = request.params
        data_payload = params.get("data_payload")
        query = params.get("query")
        
        if not data_payload:
             return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Missing data_payload"},
                "id": request.id
            }

        # Decode base64
        try:
            decoded_data = base64.b64decode(data_payload).decode('utf-8')
        except Exception as e:
             return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"Base64 decode failed: {str(e)}"},
                "id": request.id
            }

        # Load into DataFrame
        try:
            df = pd.read_csv(io.StringIO(decoded_data))
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": f"CSV parse failed: {str(e)}"},
                "id": request.id
            }

        # Run Analysis
        # Use a request ID or timestamp for file prefix to avoid collisions
        file_prefix = f"req_{request.id}"
        result_text = agent.run_analysis_pipeline(df, question=query, file_prefix=file_prefix)

        return {
            "jsonrpc": "2.0",
            "result": {"result": result_text}, # Matches agent.json output schema
            "id": request.id
        }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(e)},
            "id": request.id
        }

if __name__ == "__main__":
    # Check if running as server or CLI
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        port = int(os.getenv("PORT", "8080"))
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Keep original CLI functionality for backward compatibility tests
        if len(sys.argv) < 2:
            print("Usage: python main.py <csv_file_path> [question]")
            print("       python main.py server (to run in A2A server mode)")
            sys.exit(1)
        
        csv_path = sys.argv[1]
        question = sys.argv[2] if len(sys.argv) > 2 else None
        
        # Quick instantiation for CLI
        cli_agent = DataExplorerAgent()
        
        # Load manually for CLI
        df = cli_agent.load_csv(csv_path)
        if df is not None:
            cli_agent.run_analysis_pipeline(df, question)
